import os
import json
import hashlib
import numpy as np
import streamlit as st
from PIL import Image, ImageDraw

# ============================================================
# TEMEXY PRICE-ACTION SETUP LIBRARY (v3 — model-aware edition)
#
# This version stops treating every screenshot as "just a picture"
# and instead reconstructs an approximate candlestick series from
# the pixels, then checks it against YOUR exact model:
#
#   1. A break of structure (BOS) OR a liquidity sweep.
#   2. The leg that causes that BOS/sweep must contain an FVG
#      (fair value gap) that formed BEFORE the break/sweep point.
#   3. Before that FVG, there must be an order block (OB) — the
#      last opposite-colored candle before the impulsive leg
#      started. That OB is the entry.
#
# Because your 3 pairs behave differently, the two parameters that
# actually need to flex per instrument — swing lookback and the
# minimum FVG size (as a % of the visible price range, since we
# don't have real price data from a screenshot) — are configurable
# per market and saved to config.json.
#
# IMPORTANT HONESTY NOTE (read this before trusting the output):
# Candle extraction is done by color-segmenting pixels (green =
# bullish, near-black = bearish) and grouping columns into candles.
# It works well on a CLEAN chart screenshot. If you upload a chart
# that already has your own OB/FVG boxes drawn on it, those overlay
# colors can occasionally get misread as candle pixels. For best
# accuracy, save/query with plain candlestick screenshots and let
# this app draw the OB/FVG/BOS zones itself — that's also how you
# get a second, independent check on your own manual marking.
# ============================================================

st.set_page_config(page_title="Temexy Setup Library", page_icon="📈", layout="wide")

st.title("📚 Temexy Price-Action Setup Library — Model Edition")
st.caption(
    "Detects your exact model — BOS/liquidity sweep → FVG before the sweep → OB before "
    "the FVG — from the raw candles in a screenshot, then matches new charts against "
    "your saved library using that structure, not just visual similarity."
)

STORAGE_DIR = "setup_library"
DB_FILE = os.path.join(STORAGE_DIR, "library.json")
CONFIG_FILE = os.path.join(STORAGE_DIR, "config.json")
os.makedirs(STORAGE_DIR, exist_ok=True)

MARKETS = ["XAUUSD", "USDCHF", "BTCUSD", "Other"]

DEFAULT_PARAMS = {
    "swing_lookback": 3,     # candles on each side to confirm a swing high/low
    "min_fvg_frac": 0.03,    # minimum FVG size as a fraction of the visible price range
}

STRUCT_SIZE = (96, 96)
CELL_SIZE = 16
N_BINS = 9


# ------------------------------------------------------------
# Per-market config (persisted)
# ------------------------------------------------------------

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
    else:
        cfg = {}
    for m in MARKETS:
        cfg.setdefault(m, dict(DEFAULT_PARAMS))
    return cfg


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f)


# ------------------------------------------------------------
# Auto-crop (find the chart plot area, ignore UI margins)
# ------------------------------------------------------------

def _bounds_from_profile(profile, frac=0.15):
    if profile.max() <= 1e-6:
        return 0, len(profile)
    thresh = profile.max() * frac
    idx = np.where(profile > thresh)[0]
    if len(idx) == 0:
        return 0, len(profile)
    return int(idx[0]), int(idx[-1]) + 1


def auto_crop(img):
    gray = np.asarray(img.convert("L"), dtype=np.float32)
    h, w = gray.shape
    row_std, col_std = gray.std(axis=1), gray.std(axis=0)
    top, bottom = _bounds_from_profile(row_std)
    left, right = _bounds_from_profile(col_std)
    pad_h, pad_w = int(0.02 * h), int(0.02 * w)
    top, bottom = max(0, top - pad_h), min(h, bottom + pad_h)
    left, right = max(0, left - pad_w), min(w, right + pad_w)
    if (bottom - top) < 0.4 * h or (right - left) < 0.4 * w:
        left, top, right, bottom = int(w * 0.05), int(h * 0.10), int(w * 0.98), int(h * 0.94)
    return img.crop((left, top, right, bottom))


# ------------------------------------------------------------
# Candle extraction from pixels
# ------------------------------------------------------------

def group_columns(has_col, max_gap=1):
    groups = []
    n = len(has_col)
    i = 0
    while i < n:
        if not has_col[i]:
            i += 1
            continue
        start = end = i
        gap = 0
        j = i + 1
        while j < n:
            if has_col[j]:
                end = j
                gap = 0
            else:
                gap += 1
                if gap > max_gap:
                    break
            j += 1
        groups.append((start, end))
        i = j
    return groups


def extract_candles(color_img, min_col_pixels=2, body_coverage=0.55):
    arr = np.asarray(color_img.convert("RGB"), dtype=np.float32)
    H, W, _ = arr.shape
    R, G, B = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    is_bull = (G > R + 18) & (G > B + 18)
    is_bear = (R < 90) & (G < 90) & (B < 90)
    colored = is_bull | is_bear

    col_counts = colored.sum(axis=0)
    has_col = col_counts >= min_col_pixels
    groups = group_columns(has_col, max_gap=1)

    def to_price(y):
        return 1.0 - (y / max(H - 1, 1))

    candles = []
    for (x0, x1) in groups:
        region = colored[:, x0:x1 + 1]
        rows = np.where(region.any(axis=1))[0]
        if len(rows) == 0:
            continue
        wick_top, wick_bottom = int(rows.min()), int(rows.max())

        coverage = region.mean(axis=1)
        body_rows = np.where(coverage >= body_coverage)[0]
        if len(body_rows) == 0:
            body_top, body_bottom = wick_top, wick_bottom
        else:
            body_top, body_bottom = int(body_rows.min()), int(body_rows.max())

        bull_count = is_bull[:, x0:x1 + 1].sum()
        bear_count = is_bear[:, x0:x1 + 1].sum()
        color = "bull" if bull_count >= bear_count else "bear"

        high, low = to_price(wick_top), to_price(wick_bottom)
        body_high, body_low = to_price(body_top), to_price(body_bottom)
        close, open_ = (body_high, body_low) if color == "bull" else (body_low, body_high)

        candles.append({
            "x0": x0, "x1": x1,
            "wick_top": wick_top, "wick_bottom": wick_bottom,
            "body_top": body_top, "body_bottom": body_bottom,
            "high": high, "low": low,
            "body_high": body_high, "body_low": body_low,
            "close": close, "open": open_,
            "color": color,
        })

    return candles, H, W


# ------------------------------------------------------------
# Structure: swings, BOS, liquidity sweeps
# ------------------------------------------------------------

def find_swings(candles, lookback=3):
    n = len(candles)
    highs, lows = [], []
    for i in range(n):
        lo, hi = max(0, i - lookback), min(n, i + lookback + 1)
        window = candles[lo:hi]
        if candles[i]["high"] >= max(c["high"] for c in window):
            highs.append(i)
        if candles[i]["low"] <= min(c["low"] for c in window):
            lows.append(i)
    return highs, lows


def find_events(candles, swing_high_idx, swing_low_idx):
    """BOS = close breaks beyond a prior swing level. Sweep = wick pokes
    beyond it but the candle closes back inside (liquidity grab)."""
    events = []
    broken_highs, broken_lows = set(), set()

    for i, c in enumerate(candles):
        for sh in swing_high_idx:
            if sh >= i or sh in broken_highs:
                continue
            level = candles[sh]["high"]
            if c["high"] > level:
                broken_highs.add(sh)
                if c["close"] > level:
                    events.append({"type": "bos_bull", "idx": i, "level": level, "ref_idx": sh})
                else:
                    events.append({"type": "sweep_high", "idx": i, "level": level, "ref_idx": sh})
        for sl in swing_low_idx:
            if sl >= i or sl in broken_lows:
                continue
            level = candles[sl]["low"]
            if c["low"] < level:
                broken_lows.add(sl)
                if c["close"] < level:
                    events.append({"type": "bos_bear", "idx": i, "level": level, "ref_idx": sl})
                else:
                    events.append({"type": "sweep_low", "idx": i, "level": level, "ref_idx": sl})
    return events


# ------------------------------------------------------------
# FVG (fair value gap): 3-candle imbalance
# ------------------------------------------------------------

def find_fvgs(candles, min_fvg_frac):
    if not candles:
        return []
    total_range = max(c["high"] for c in candles) - min(c["low"] for c in candles)
    total_range = max(total_range, 1e-6)
    fvgs = []
    for i in range(1, len(candles) - 1):
        c1, c3 = candles[i - 1], candles[i + 1]
        if c1["high"] < c3["low"]:
            size = c3["low"] - c1["high"]
            if size >= min_fvg_frac * total_range:
                fvgs.append({"type": "bull", "idx1": i - 1, "idx3": i + 1, "top": c3["low"], "bottom": c1["high"]})
        elif c1["low"] > c3["high"]:
            size = c1["low"] - c3["high"]
            if size >= min_fvg_frac * total_range:
                fvgs.append({"type": "bear", "idx1": i - 1, "idx3": i + 1, "top": c1["low"], "bottom": c3["high"]})
    return fvgs


# ------------------------------------------------------------
# OB (order block): last opposite-color candle before a leg
# ------------------------------------------------------------

def find_ob(candles, leg_origin_idx, direction):
    opposite = "bear" if direction == "bull" else "bull"
    for j in range(leg_origin_idx, -1, -1):
        if candles[j]["color"] == opposite:
            return j
    return None


# ------------------------------------------------------------
# Full sequence: BOS/sweep -> FVG before it -> OB before that
# ------------------------------------------------------------

def detect_model_setups(candles, params):
    if len(candles) < 6:
        return []

    swing_high_idx, swing_low_idx = find_swings(candles, lookback=params["swing_lookback"])
    events = find_events(candles, swing_high_idx, swing_low_idx)
    fvgs = find_fvgs(candles, params["min_fvg_frac"])
    total_range = max(c["high"] for c in candles) - min(c["low"] for c in candles)
    total_range = max(total_range, 1e-6)

    setups = []
    for ev in events:
        direction = "bull" if ev["type"] in ("bos_bull", "sweep_high") else "bear"
        event_idx = ev["idx"]

        matching_fvgs = [f for f in fvgs if f["type"] == direction and f["idx3"] <= event_idx]
        if not matching_fvgs:
            continue
        fvg = max(matching_fvgs, key=lambda f: f["idx3"])

        ob_idx = find_ob(candles, fvg["idx1"], direction)
        if ob_idx is None:
            continue
        ob = candles[ob_idx]

        setups.append({
            "direction": direction,
            "is_sweep": ev["type"] in ("sweep_high", "sweep_low"),
            "event_idx": event_idx,
            "event_level": ev["level"],
            "fvg": fvg,
            "ob_idx": ob_idx,
            "ob_size": abs(ob["body_high"] - ob["body_low"]) / total_range,
            "fvg_size": (fvg["top"] - fvg["bottom"]) / total_range,
            "leg_len": (event_idx - ob_idx) / max(len(candles), 1),
            "displacement": abs(candles[event_idx]["close"] - ev["level"]) / total_range,
        })

    return setups


def pick_primary_setup(setups):
    """Pick the setup with the largest FVG (clearest imbalance) as the
    representative one for this chart."""
    if not setups:
        return None
    return max(setups, key=lambda s: s["fvg_size"])


def struct_vector(setup):
    return np.array([
        setup["ob_size"], setup["fvg_size"], setup["leg_len"],
        setup["displacement"], 1.0 if setup["is_sweep"] else 0.0,
    ], dtype=np.float32)


def struct_similarity(a, b):
    """1 / (1 + distance) over the 4 continuous stats, direction and
    sweep-vs-bos are hard-matched separately, not blended in here."""
    dist = float(np.linalg.norm(np.asarray(a[:4]) - np.asarray(b[:4])))
    return 1.0 / (1.0 + dist)


# ------------------------------------------------------------
# Overlay drawing so you can SEE what got detected
# ------------------------------------------------------------

def draw_annotated(color_img, candles, H, setup):
    img = color_img.convert("RGB").copy()
    draw = ImageDraw.Draw(img, "RGBA")

    def y_of(price):
        return int((1.0 - price) * (H - 1))

    ob = candles[setup["ob_idx"]]
    ob_end_x = candles[setup["fvg"]["idx1"]]["x1"]
    draw.rectangle(
        [ob["x0"] - 2, y_of(max(ob["body_high"], ob["body_low"])), ob_end_x + 2, y_of(min(ob["body_high"], ob["body_low"]))],
        outline=(255, 140, 0, 255), fill=(255, 140, 0, 60), width=2,
    )
    draw.text((ob["x0"], y_of(max(ob["body_high"], ob["body_low"])) - 14), "OB", fill=(200, 90, 0, 255))

    fvg = setup["fvg"]
    fvg_end_x = candles[setup["event_idx"]]["x1"]
    draw.rectangle(
        [candles[fvg["idx1"]]["x0"] - 1, y_of(fvg["top"]), fvg_end_x + 2, y_of(fvg["bottom"])],
        outline=(30, 120, 255, 255), fill=(30, 120, 255, 60), width=2,
    )
    draw.text((candles[fvg["idx1"]]["x0"], y_of(fvg["top"]) - 14), "FVG", fill=(20, 90, 200, 255))

    event_x = candles[setup["event_idx"]]["x1"]
    label = "SWEEP" if setup["is_sweep"] else "BOS"
    draw.line([(event_x, 0), (event_x, H)], fill=(220, 0, 0, 200), width=1)
    draw.text((event_x + 3, 4), label, fill=(200, 0, 0, 255))

    return img


# ------------------------------------------------------------
# Lightweight visual descriptor (secondary tiebreaker only)
# ------------------------------------------------------------

def resize_and_center_crop(img, size):
    target_w, target_h = size
    w, h = img.size
    scale = max(target_w / w, target_h / h)
    nw, nh = max(target_w, int(w * scale)), max(target_h, int(h * scale))
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = max(0, (nw - target_w) // 2), max(0, (nh - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def normalized_gray_array(img, size=STRUCT_SIZE):
    gray = resize_and_center_crop(img, size).convert("L")
    arr = np.asarray(gray, dtype=np.float32) / 255.0
    arr = (arr - arr.mean()) / (arr.std() + 1e-6)
    arr = np.clip(arr, -3.0, 3.0)
    return (arr - arr.min()) / (arr.max() - arr.min() + 1e-6)


def compute_hog(gray_arr, cell_size=CELL_SIZE, n_bins=N_BINS):
    gy, gx = np.gradient(gray_arr.astype(np.float32))
    magnitude = np.sqrt(gx * gx + gy * gy)
    angle = np.degrees(np.arctan2(gy, gx)) % 180.0
    h, w = gray_arr.shape
    n_cells_y, n_cells_x = h // cell_size, w // cell_size
    bin_width = 180.0 / n_bins
    hist = np.zeros((n_cells_y, n_cells_x, n_bins), dtype=np.float32)
    bin_idx = np.minimum((angle // bin_width).astype(int), n_bins - 1)
    for cy in range(n_cells_y):
        for cx in range(n_cells_x):
            y0, y1 = cy * cell_size, (cy + 1) * cell_size
            x0, x1 = cx * cell_size, (cx + 1) * cell_size
            cb = bin_idx[y0:y1, x0:x1].ravel()
            cm = magnitude[y0:y1, x0:x1].ravel()
            hist[cy, cx, :] = np.bincount(cb, weights=cm, minlength=n_bins)[:n_bins]
    vec = hist.ravel()
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 1e-6 else vec


def cosine(a, b):
    a, b = np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-6
    return float(np.dot(a, b) / denom)


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


def file_hash(uploaded_file):
    return hashlib.sha256(uploaded_file.getvalue()).hexdigest()


def analyze_image(pil_img, params):
    cropped = auto_crop(pil_img.convert("RGB"))
    candles, H, W = extract_candles(cropped)
    setups = detect_model_setups(candles, params)
    primary = pick_primary_setup(setups)
    gray_arr = normalized_gray_array(cropped)
    visual = compute_hog(gray_arr).tolist()
    return {
        "cropped": cropped, "candles": candles, "H": H, "W": W,
        "setups": setups, "primary": primary, "visual": visual,
    }


db = load_db()
config = load_config()

# ------------------------------------------------------------
# Sidebar: per-market model parameters
# ------------------------------------------------------------

st.sidebar.header("⚙️ Model Parameters (per pair)")
tune_market = st.sidebar.selectbox("Tune parameters for", MARKETS, key="tune_market")
mp = config[tune_market]
new_lookback = st.sidebar.slider("Swing lookback (candles)", 1, 6, mp["swing_lookback"], key="lb")
new_fvg_frac = st.sidebar.slider("Min FVG size (% of visible range)", 1, 15, int(mp["min_fvg_frac"] * 100), key="fvgpct")
if st.sidebar.button("💾 Save parameters for " + tune_market):
    config[tune_market] = {"swing_lookback": new_lookback, "min_fvg_frac": new_fvg_frac / 100.0}
    save_config(config)
    st.sidebar.success(f"Saved parameters for {tune_market}")

st.sidebar.markdown("---")
st.sidebar.header("➕ Add Historical Setup")
uploaded = st.sidebar.file_uploader("Upload setup screenshot", type=["png", "jpg", "jpeg"], key="library_upload")
pair = st.sidebar.selectbox("Market", MARKETS, key="save_market")
timeframe = st.sidebar.selectbox("Timeframe", ["1M", "5M", "15M", "30M", "1H", "4H", "Daily", "Other"])
result = st.sidebar.selectbox("Backtest result", ["Win", "Loss", "Break-even", "Testing / Unknown"])
session = st.sidebar.selectbox("Session", ["Asia / Tokyo", "London", "New York", "Overlap", "Unknown"])
notes = st.sidebar.text_area("Optional notes")

if uploaded is not None:
    preview_img = Image.open(uploaded)
    params = config[pair]
    analysis = analyze_image(preview_img, params)

    if analysis["primary"] is None:
        st.sidebar.warning(
            "No full OB → FVG → BOS/sweep sequence detected with current parameters. "
            "You can still save it, but it won't count as a strict model match later. "
            "Try loosening the FVG size or swing lookback for this pair."
        )
    else:
        annotated = draw_annotated(analysis["cropped"], analysis["candles"], analysis["H"], analysis["primary"])
        st.sidebar.image(annotated, caption="Detected OB / FVG / event — check this before saving", use_container_width=True)

    if st.sidebar.button("💾 Save Setup"):
        content_hash = file_hash(uploaded)
        duplicate = next((sid for sid, item in db.items() if item.get("file_hash") == content_hash), None)
        if duplicate:
            st.sidebar.warning(f"Already saved as {duplicate}.")
        else:
            setup_id = new_id(db)
            img_path = os.path.join(STORAGE_DIR, f"{setup_id}.png")
            analysis["cropped"].convert("RGB").save(img_path, "PNG")

            annotated_path = None
            if analysis["primary"] is not None:
                annotated_path = os.path.join(STORAGE_DIR, f"{setup_id}_annotated.png")
                draw_annotated(analysis["cropped"], analysis["candles"], analysis["H"], analysis["primary"]).save(annotated_path, "PNG")

            db[setup_id] = {
                "market": pair, "timeframe": timeframe, "result": result,
                "session": session, "notes": notes, "image": img_path,
                "annotated_image": annotated_path, "file_hash": content_hash,
                "visual": analysis["visual"],
                "struct": struct_vector(analysis["primary"]).tolist() if analysis["primary"] else None,
                "direction": analysis["primary"]["direction"] if analysis["primary"] else None,
                "is_sweep": analysis["primary"]["is_sweep"] if analysis["primary"] else None,
                "valid_model": analysis["primary"] is not None,
            }
            save_db(db)
            st.sidebar.success(f"Saved as {setup_id}" + ("" if analysis["primary"] else " (no valid model detected)"))

st.sidebar.markdown("---")
st.sidebar.metric("Saved setups", len(db))
valid_count = sum(1 for v in db.values() if v.get("valid_model"))
st.sidebar.caption(f"{valid_count} of {len(db)} have a confirmed OB→FVG→BOS/sweep sequence.")

st.sidebar.markdown("---")
st.sidebar.subheader("🗑️ Manage Library")
if db:
    del_id = st.sidebar.selectbox("Select setup to delete", list(db.keys()), key="del_select")
    if st.sidebar.button("Delete selected setup"):
        for key in ("image", "annotated_image"):
            p = db[del_id].get(key)
            if p and os.path.exists(p):
                os.remove(p)
        del db[del_id]
        save_db(db)
        st.sidebar.success(f"Deleted {del_id}")
        st.rerun()

# ------------------------------------------------------------
# Main: query a new chart
# ------------------------------------------------------------

st.header("🔎 Check a New Chart Against the Model")

query_market = st.selectbox("Market of the chart you're checking", MARKETS, key="query_market")
query_file = st.file_uploader("Upload the chart to analyze", type=["png", "jpg", "jpeg"], key="query_upload")

strict_mode = st.checkbox("Strict mode: only show library matches that also have a confirmed model sequence", value=True)
same_timeframe_only = st.checkbox("Only compare within same timeframe", value=False)
top_n = st.slider("Max matches to show", 3, 12, 6)

if query_file:
    query_img = Image.open(query_file)
    params = config[query_market]
    analysis = analyze_image(query_img, params)

    st.subheader("Detected on your chart")
    if analysis["primary"] is None:
        st.error(
            "No OB → FVG → BOS/liquidity-sweep sequence detected on this chart with the "
            f"current {query_market} parameters. Either the model genuinely isn't present here, "
            "or the parameters need adjusting in the sidebar for this pair."
        )
        st.image(analysis["cropped"], use_container_width=True)
    else:
        p = analysis["primary"]
        annotated = draw_annotated(analysis["cropped"], analysis["candles"], analysis["H"], p)
        st.image(annotated, use_container_width=True)
        st.success(
            f"Detected a **{p['direction'].upper()}** setup "
            f"({'liquidity sweep' if p['is_sweep'] else 'break of structure'}) — "
            f"OB size {p['ob_size']*100:.1f}% · FVG size {p['fvg_size']*100:.1f}% of visible range."
        )
        st.caption("This OB zone (orange) is your suggested entry on THIS chart — it's independent of any saved example's entry point.")

        if not db:
            st.warning("Library is empty — nothing to compare against yet.")
        else:
            candidates = [(sid, item) for sid, item in db.items() if item.get("market") == query_market]
            if same_timeframe_only:
                candidates = [(sid, item) for sid, item in candidates if item.get("timeframe") == analysis.get("timeframe")]
            if strict_mode:
                candidates = [(sid, item) for sid, item in candidates if item.get("valid_model")]

            q_struct = struct_vector(p)
            scored = []
            for sid, item in candidates:
                if item.get("valid_model") and item.get("struct") is not None:
                    if item.get("direction") != p["direction"] or bool(item.get("is_sweep")) != p["is_sweep"]:
                        continue
                    s_score = struct_similarity(q_struct, np.array(item["struct"]))
                    v_score = cosine(analysis["visual"], item["visual"])
                    total = 0.85 * s_score + 0.15 * max(0.0, v_score)
                else:
                    total = 0.15 * max(0.0, cosine(analysis["visual"], item["visual"]))
                scored.append({"id": sid, "score": total, "item": item})

            scored.sort(key=lambda x: x["score"], reverse=True)
            scored = scored[:top_n]

            st.markdown("---")
            st.subheader(f"📁 Closest matches in your {query_market} library")
            if not scored:
                st.info("No comparable setups found under the current filters.")
            for start in range(0, len(scored), 3):
                row = scored[start:start + 3]
                cols = st.columns(len(row))
                for col, m in zip(cols, row):
                    with col:
                        item = m["item"]
                        st.markdown(f"**{m['id']}** — {m['score']*100:.0f}% match")
                        show_path = item.get("annotated_image") or item.get("image")
                        if show_path and os.path.exists(show_path):
                            st.image(show_path, use_container_width=True)
                        tag = "✅ Confirmed model" if item.get("valid_model") else "⚠️ No confirmed sequence"
                        st.caption(tag)
                        st.write(f"**Timeframe:** {item.get('timeframe')} · **Result:** {item.get('result')}")
                        st.write(f"**Session:** {item.get('session')}")
                        if item.get("notes"):
                            st.caption(item["notes"])

# ------------------------------------------------------------
# Library browser
# ------------------------------------------------------------

st.markdown("---")
st.header("🗂️ Your Setup Library")

if db:
    browser_cols = st.columns(4)
    for idx, (sid, item) in enumerate(db.items()):
        with browser_cols[idx % 4]:
            show_path = item.get("annotated_image") or item.get("image")
            if show_path and os.path.exists(show_path):
                st.image(show_path, use_container_width=True)
            st.markdown(f"**{sid}**")
            tag = "✅" if item.get("valid_model") else "⚠️"
            st.caption(f"{tag} {item.get('market')} · {item.get('timeframe')} · {item.get('result')}")
else:
    st.write("No setups saved yet.")

st.markdown("---")
st.caption(
    "TEMEXY LIBRARY v3 — OB → FVG → BOS/sweep detection reconstructed from screenshot "
    "pixels. This is a heuristic reader of your charts, not a price-data feed — always "
    "confirm the drawn zones match what you see before acting on them."
)
