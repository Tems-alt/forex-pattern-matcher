import os
import json
import hashlib
import numpy as np
import streamlit as st
from PIL import Image

# ============================================================
# TEMEXY PRICE-ACTION SETUP LIBRARY (v2 — "strict" edition)
#
# What changed vs the first version, and why it matters for
# backtesting:
#
#   1. Auto-crop detects the actual chart plot area (instead of
#      a fixed 5%/10% margin), so TradingView UI/toolbar noise
#      stops polluting the comparison.
#
#   2. Real structural features: an HOG-style gradient-orientation
#      descriptor captures the SHAPE of candle wicks/bodies/swings,
#      not just raw pixel brightness. This is the main reason the
#      old version felt "not good enough" — pixel + simple-gradient
#      averages are very easy to fool.
#
#   3. A separate "candle rhythm" descriptor looks at the green/red
#      balance and volatility column-by-column, so a bullish
#      structure won't casually match a bearish one that merely
#      LOOKS similar in grayscale.
#
#   4. Multiple crop variants (tight/base/loose) are stored per
#      setup and compared pairwise, so small differences in how
#      you screenshot a chart don't tank the score.
#
#   5. A confidence threshold + optional market/timeframe filters
#      make the tool "strict" by default: weak/irrelevant matches
#      are hidden unless you ask to see them, and you get a
#      per-component score breakdown instead of one vague number.
#
# This still does NOT predict whether a trade will win. It is a
# retrieval tool: it finds structurally/rhythmically similar past
# setups from YOUR library so you can judge for yourself.
# ============================================================

st.set_page_config(page_title="Temexy Setup Library", page_icon="📈", layout="wide")

st.title("📚 Temexy Price-Action Setup Library")
st.caption(
    "Save a setup once you've taken/analysed it. Later, paste a new chart and the "
    "library tells you — with a confidence score and a breakdown — whether it has "
    "seen something structurally similar before."
)

STORAGE_DIR = "setup_library"
DB_FILE = os.path.join(STORAGE_DIR, "library.json")
os.makedirs(STORAGE_DIR, exist_ok=True)

STRUCT_SIZE = (96, 96)       # size used for the HOG / shape descriptors
CELL_SIZE = 16               # HOG cell size in pixels -> 6x6 cells on 96x96
N_BINS = 9                   # unsigned HOG orientation bins
RHYTHM_COLS = 48             # columns used for the candle-rhythm descriptor

# Crop-tightness multipliers used to build the 3 stored variants.
VARIANT_PAD_SCALES = {"tight": 0.5, "base": 1.0, "loose": 1.7}

# Weights for the final blended score. These are tuned so that
# structure (shape of the move) dominates, rhythm (bull/bear balance)
# matters a lot for direction-sensitive setups, and the coarse shape
# vector acts as a tie-breaker / sanity check.
WEIGHTS = {"structure": 0.5, "rhythm": 0.3, "shape": 0.2}


# ------------------------------------------------------------
# Auto-crop: find the actual chart area instead of guessing
# fixed margins.
# ------------------------------------------------------------

def _bounds_from_profile(profile, frac=0.15):
    if profile.max() <= 1e-6:
        return 0, len(profile)
    thresh = profile.max() * frac
    idx = np.where(profile > thresh)[0]
    if len(idx) == 0:
        return 0, len(profile)
    return int(idx[0]), int(idx[-1]) + 1


def auto_crop_bounds(img, pad_scale=1.0):
    """Return (left, top, right, bottom) for the detected chart area."""
    gray = np.asarray(img.convert("L"), dtype=np.float32)
    h, w = gray.shape

    row_std = gray.std(axis=1)
    col_std = gray.std(axis=0)

    top, bottom = _bounds_from_profile(row_std)
    left, right = _bounds_from_profile(col_std)

    pad_h = int(0.02 * h * pad_scale)
    pad_w = int(0.02 * w * pad_scale)

    top = max(0, top - pad_h)
    bottom = min(h, bottom + pad_h)
    left = max(0, left - pad_w)
    right = min(w, right + pad_w)

    # Sanity fallback: if detection collapsed too aggressively,
    # fall back to a conservative fixed crop.
    if (bottom - top) < 0.4 * h or (right - left) < 0.4 * w:
        left, top, right, bottom = int(w * 0.05), int(h * 0.10), int(w * 0.98), int(h * 0.94)

    return left, top, right, bottom


def crop_variant(img, pad_scale):
    left, top, right, bottom = auto_crop_bounds(img, pad_scale)
    if right <= left or bottom <= top:
        return img
    return img.crop((left, top, right, bottom))


def resize_and_center_crop(img, size):
    """Resize preserving aspect ratio, then center-crop to `size`."""
    target_w, target_h = size
    w, h = img.size
    scale = max(target_w / w, target_h / h)
    nw, nh = max(target_w, int(w * scale)), max(target_h, int(h * scale))
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, (nw - target_w) // 2)
    top = max(0, (nh - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def normalized_gray_array(cropped_img, size=STRUCT_SIZE):
    gray = resize_and_center_crop(cropped_img, size).convert("L")
    arr = np.asarray(gray, dtype=np.float32) / 255.0
    arr = (arr - arr.mean()) / (arr.std() + 1e-6)
    arr = np.clip(arr, -3.0, 3.0)
    arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-6)
    return arr


# ------------------------------------------------------------
# Descriptor 1: HOG-style gradient-orientation histogram.
# Captures the SHAPE of the price action (swing highs/lows,
# wick/body geometry) far better than raw pixel comparison.
# ------------------------------------------------------------

def compute_hog(gray_arr, cell_size=CELL_SIZE, n_bins=N_BINS):
    gy, gx = np.gradient(gray_arr.astype(np.float32))
    magnitude = np.sqrt(gx * gx + gy * gy)
    angle = np.degrees(np.arctan2(gy, gx)) % 180.0  # unsigned

    h, w = gray_arr.shape
    n_cells_y, n_cells_x = h // cell_size, w // cell_size
    bin_width = 180.0 / n_bins

    hist = np.zeros((n_cells_y, n_cells_x, n_bins), dtype=np.float32)
    bin_idx = np.minimum((angle // bin_width).astype(int), n_bins - 1)

    for cy in range(n_cells_y):
        for cx in range(n_cells_x):
            y0, y1 = cy * cell_size, (cy + 1) * cell_size
            x0, x1 = cx * cell_size, (cx + 1) * cell_size
            cell_bins = bin_idx[y0:y1, x0:x1].ravel()
            cell_mag = magnitude[y0:y1, x0:x1].ravel()
            hist[cy, cx, :] = np.bincount(cell_bins, weights=cell_mag, minlength=n_bins)[:n_bins]

    vec = hist.ravel()
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 1e-6 else vec


# ------------------------------------------------------------
# Descriptor 2: coarse shape (low-res grayscale) — a cheap
# sanity-check signal, mostly a tie-breaker alongside HOG.
# ------------------------------------------------------------

def compute_shape(gray_arr, size=(20, 20)):
    img = Image.fromarray(np.uint8(np.clip(gray_arr, 0, 1) * 255))
    small = np.asarray(img.resize(size, Image.Resampling.BILINEAR), dtype=np.float32) / 255.0
    vec = small.ravel()
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 1e-6 else vec


# ------------------------------------------------------------
# Descriptor 3: candle rhythm — green/red balance and
# brightness (volatility proxy) per horizontal column, so a
# bullish leg doesn't get confused with a bearish one.
# ------------------------------------------------------------

def compute_rhythm(cropped_color_img, bins=RHYTHM_COLS):
    small = cropped_color_img.convert("RGB").resize((bins, 32), Image.Resampling.LANCZOS)
    arr = np.asarray(small, dtype=np.float32) / 255.0
    r, g = arr[:, :, 0], arr[:, :, 1]
    green_minus_red = (g - r).mean(axis=0)
    brightness = arr.mean(axis=(0, 2))
    vec = np.concatenate([green_minus_red, brightness]).astype(np.float32)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 1e-6 else vec


# ------------------------------------------------------------
# Full feature extraction for one image: 3 crop variants,
# each with an HOG + shape vector, plus one rhythm vector
# from the base crop.
# ------------------------------------------------------------

def extract_features(img):
    img = img.convert("RGB")
    variants = []
    for name, pad_scale in VARIANT_PAD_SCALES.items():
        cropped = crop_variant(img, pad_scale)
        gray_arr = normalized_gray_array(cropped)
        variants.append({
            "name": name,
            "hog": compute_hog(gray_arr).tolist(),
            "shape": compute_shape(gray_arr).tolist(),
        })

    base_cropped = crop_variant(img, VARIANT_PAD_SCALES["base"])
    rhythm = compute_rhythm(base_cropped).tolist()

    return {"variants": variants, "rhythm": rhythm}


def cosine(a, b):
    a, b = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-6
    return float(np.dot(a, b) / denom)


def match_score(query_feat, item_feat):
    """Best-of-variants structure/shape score + single rhythm score."""
    best_structure = max(
        cosine(qv["hog"], iv["hog"])
        for qv in query_feat["variants"]
        for iv in item_feat["variants"]
    )
    best_shape = max(
        cosine(qv["shape"], iv["shape"])
        for qv in query_feat["variants"]
        for iv in item_feat["variants"]
    )
    rhythm = cosine(query_feat["rhythm"], item_feat["rhythm"])

    # cosine can be slightly negative; clip to a 0..1 scale for display.
    structure = max(0.0, best_structure)
    shape = max(0.0, best_shape)
    rhythm_c = max(0.0, rhythm)

    total = (
        WEIGHTS["structure"] * structure
        + WEIGHTS["rhythm"] * rhythm_c
        + WEIGHTS["shape"] * shape
    )
    return total, {"structure": structure, "rhythm": rhythm_c, "shape": shape}


# ------------------------------------------------------------
# Database
# ------------------------------------------------------------

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f)


def new_id(db):
    n = 1
    while f"SETUP_{n:04d}" in db:
        n += 1
    return f"SETUP_{n:04d}"


def save_image(img, setup_id):
    path = os.path.join(STORAGE_DIR, f"{setup_id}.png")
    img.convert("RGB").save(path, "PNG")
    return path


def file_hash(uploaded_file):
    return hashlib.sha256(uploaded_file.getvalue()).hexdigest()


db = load_db()

# ------------------------------------------------------------
# Sidebar: add setup
# ------------------------------------------------------------

st.sidebar.header("➕ Add Historical Setup")

uploaded = st.sidebar.file_uploader("Upload setup screenshot", type=["png", "jpg", "jpeg"], key="library_upload")
pair = st.sidebar.selectbox("Market", ["XAUUSD", "USDCHF", "BTCUSD", "Other"])
timeframe = st.sidebar.selectbox("Timeframe", ["1M", "5M", "15M", "30M", "1H", "4H", "Daily", "Other"])
direction = st.sidebar.selectbox("Direction", ["Buy", "Sell", "Unknown / Don't care"])
result = st.sidebar.selectbox("Backtest result", ["Win", "Loss", "Break-even", "Testing / Unknown"])
session = st.sidebar.selectbox("Session", ["Asia / Tokyo", "London", "New York", "Overlap", "Unknown"])
notes = st.sidebar.text_area("Optional notes", placeholder="What did you notice about this setup?")

if st.sidebar.button("💾 Save Setup"):
    if uploaded is None:
        st.sidebar.error("Upload a screenshot first.")
    else:
        try:
            content_hash = file_hash(uploaded)
            duplicate = next((sid for sid, item in db.items() if item.get("file_hash") == content_hash), None)

            if duplicate:
                st.sidebar.warning(f"This screenshot is already saved as {duplicate}.")
            else:
                img = Image.open(uploaded).convert("RGB")
                setup_id = new_id(db)
                image_path = save_image(img, setup_id)
                features = extract_features(img)

                db[setup_id] = {
                    "market": pair,
                    "timeframe": timeframe,
                    "direction": direction,
                    "result": result,
                    "session": session,
                    "notes": notes,
                    "image": image_path,
                    "file_hash": content_hash,
                    "features": features,
                }
                save_db(db)
                st.sidebar.success(f"Saved as {setup_id}")
        except Exception as e:
            st.sidebar.error(f"Could not save setup: {e}")

st.sidebar.markdown("---")
st.sidebar.metric("Saved setups", len(db))

st.sidebar.markdown("---")
st.sidebar.subheader("🗑️ Manage Library")
if db:
    del_id = st.sidebar.selectbox("Select setup to delete", list(db.keys()), key="del_select")
    if st.sidebar.button("Delete selected setup"):
        img_path = db[del_id].get("image")
        if img_path and os.path.exists(img_path):
            os.remove(img_path)
        del db[del_id]
        save_db(db)
        st.sidebar.success(f"Deleted {del_id}")
        st.rerun()
else:
    st.sidebar.caption("Nothing to manage yet.")

# ------------------------------------------------------------
# Main: search library
# ------------------------------------------------------------

st.header("🔎 Find Similar Historical Setups")

query_file = st.file_uploader("Upload the new chart/setup you want to compare", type=["png", "jpg", "jpeg"], key="query_upload")

col_a, col_b, col_c = st.columns(3)
with col_a:
    threshold = st.slider("Minimum confidence to count as a match (%)", 40, 95, 72)
with col_b:
    same_market_only = st.checkbox("Only compare within same market", value=True)
with col_c:
    same_timeframe_only = st.checkbox("Only compare within same timeframe", value=True)

top_n = st.slider("Max matches to show", min_value=3, max_value=12, value=6)

if query_file:
    query_img = Image.open(query_file).convert("RGB")

    st.subheader("Current Setup")
    st.image(query_img, use_container_width=True)

    if not db:
        st.warning("Your setup library is empty. Save some historical setups first.")
    else:
        with st.spinner("Comparing structure, rhythm and shape..."):
            query_feature = extract_features(query_img)

            candidates = db.items()
            if same_market_only:
                candidates = [(sid, item) for sid, item in candidates if item.get("market") == pair]
            if same_timeframe_only:
                candidates = [(sid, item) for sid, item in candidates if item.get("timeframe") == timeframe]

            scored = []
            for sid, item in candidates:
                try:
                    total, breakdown = match_score(query_feature, item["features"])
                    scored.append({
                        "id": sid, "score": total, "breakdown": breakdown,
                        "market": item.get("market", "Unknown"),
                        "timeframe": item.get("timeframe", "Unknown"),
                        "direction": item.get("direction", "Unknown"),
                        "result": item.get("result", "Unknown"),
                        "session": item.get("session", "Unknown"),
                        "notes": item.get("notes", ""),
                        "image": item.get("image"),
                    })
                except Exception:
                    continue

            scored.sort(key=lambda x: x["score"], reverse=True)
            strong = [m for m in scored if m["score"] * 100 >= threshold][:top_n]
            weak = [m for m in scored if m["score"] * 100 < threshold][:top_n]

        if same_market_only or same_timeframe_only:
            st.caption(f"Compared against {len(candidates)} filtered setup(s) out of {len(db)} total.")

        def render_match(match):
            st.markdown(f"### {match['id']}")
            if match["image"] and os.path.exists(match["image"]):
                st.image(match["image"], use_container_width=True)
            st.markdown(f"**Confidence:** `{match['score'] * 100:.1f}%`")
            b = match["breakdown"]
            st.caption(
                f"Structure {b['structure']*100:.0f}% · "
                f"Rhythm {b['rhythm']*100:.0f}% · "
                f"Shape {b['shape']*100:.0f}%"
            )
            st.write(f"**Market:** {match['market']}  ·  **Timeframe:** {match['timeframe']}")
            st.write(f"**Direction:** {match['direction']}  ·  **Result:** {match['result']}")
            st.write(f"**Session:** {match['session']}")
            if match["notes"]:
                st.caption(match["notes"])

        if strong:
            st.success(f"Found {len(strong)} setup(s) at or above {threshold}% confidence.")
            for start in range(0, len(strong), 3):
                row = strong[start:start + 3]
                cols = st.columns(len(row))
                for col, match in zip(cols, row):
                    with col:
                        render_match(match)
        else:
            st.warning(f"No setups reached {threshold}% confidence. Lower the threshold or add more history.")

        if weak:
            with st.expander(f"Show {len(weak)} weaker match(es) below {threshold}%"):
                for start in range(0, len(weak), 3):
                    row = weak[start:start + 3]
                    cols = st.columns(len(row))
                    for col, match in zip(cols, row):
                        with col:
                            render_match(match)

        st.info(
            "This is a visual/structural retrieval score, not a probability of winning. "
            "It tells you what looked similar historically — the trade decision is still yours."
        )

        # ----------------------------------------------------
        # Historical summary (based on strong matches only)
        # ----------------------------------------------------
        st.markdown("---")
        st.header("📊 What the Matched Setups Tell You")

        known = [m for m in strong if m["result"] in ["Win", "Loss", "Break-even"]]
        if known:
            wins = sum(m["result"] == "Win" for m in known)
            losses = sum(m["result"] == "Loss" for m in known)
            be = sum(m["result"] == "Break-even" for m in known)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Matched examples", len(known))
            c2.metric("Wins", wins)
            c3.metric("Losses", losses)
            c4.metric("Break-even", be)
            st.caption("Descriptive history from the strong matches only — not a prediction.")
        else:
            st.write("No completed outcomes recorded among the strong matches.")

# ------------------------------------------------------------
# Library browser
# ------------------------------------------------------------

st.markdown("---")
st.header("🗂️ Your Setup Library")

if db:
    browser_cols = st.columns(4)
    for idx, (sid, item) in enumerate(db.items()):
        with browser_cols[idx % 4]:
            if item.get("image") and os.path.exists(item["image"]):
                st.image(item["image"], use_container_width=True)
            st.markdown(f"**{sid}**")
            st.caption(f"{item.get('market')} · {item.get('timeframe')} · {item.get('direction')} · {item.get('result')}")
else:
    st.write("No setups saved yet.")

st.markdown("---")
st.caption(
    "TEMEXY LIBRARY v2 — structural (HOG) + candle-rhythm retrieval with a confidence "
    "threshold. Always inspect the actual chart before making a trading decision."
)
