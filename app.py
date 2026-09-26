import os
import json
import hashlib
import numpy as np
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter

# ============================================================
# TEMEXY PRICE-ACTION SETUP LIBRARY
# Visual retrieval for backtesting.
#
# This version does NOT decide whether a setup is valid.
# It retrieves historically similar chart formations.
# ============================================================

st.set_page_config(
    page_title="Temexy Setup Library",
    page_icon="📈",
    layout="wide"
)

st.title("📚 Temexy Price-Action Setup Library")
st.caption(
    "Upload a historical setup, then later upload a new chart. "
    "The app searches your library for visually similar price-action formations."
)

STORAGE_DIR = "setup_library"
DB_FILE = os.path.join(STORAGE_DIR, "library.json")
os.makedirs(STORAGE_DIR, exist_ok=True)

# ------------------------------------------------------------
# Image preprocessing
# ------------------------------------------------------------

def crop_chart(img):
    """Remove a rough amount of TradingView UI while keeping chart structure."""
    img = img.convert("RGB")
    w, h = img.size

    # Conservative crop. Users can also upload tightly cropped charts.
    left = int(w * 0.05)
    top = int(h * 0.10)
    right = int(w * 0.98)
    bottom = int(h * 0.94)

    if right <= left or bottom <= top:
        return img

    return img.crop((left, top, right, bottom))


def make_structure_image(img, size=(96, 96)):
    """
    Create a normalized grayscale representation.
    This deliberately reduces dependence on TradingView colors/theme.
    """
    img = crop_chart(img)
    gray = img.convert("L")

    # Improve contrast and lightly sharpen edges.
    gray = ImageEnhance.Contrast(gray).enhance(2.2)
    gray = gray.filter(ImageFilter.SHARPEN)

    # Normalize dimensions so comparisons are consistent.
    gray = ImageOps_fit(gray, size)

    arr = np.asarray(gray, dtype=np.float32) / 255.0

    # Local contrast normalization.
    arr = (arr - arr.mean()) / (arr.std() + 1e-6)
    arr = np.clip(arr, -3.0, 3.0)
    arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-6)

    return arr


def ImageOps_fit(img, size):
    """Resize while preserving aspect ratio, then center crop."""
    target_w, target_h = size
    w, h = img.size

    scale = max(target_w / w, target_h / h)
    nw = max(target_w, int(w * scale))
    nh = max(target_h, int(h * scale))

    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)

    left = max(0, (nw - target_w) // 2)
    top = max(0, (nh - target_h) // 2)

    return resized.crop((left, top, left + target_w, top + target_h))


# ------------------------------------------------------------
# Feature extraction
# ------------------------------------------------------------

def gradient_features(arr):
    """
    Edge/shape information helps reduce dependence on chart colors.
    """
    gx = np.diff(arr, axis=1)
    gy = np.diff(arr, axis=0)

    # Pad to same dimensions.
    gx = np.pad(gx, ((0, 0), (0, 1)))
    gy = np.pad(gy, ((0, 1), (0, 0)))

    magnitude = np.sqrt(gx * gx + gy * gy)

    return magnitude


def downsample(arr, size=(32, 32)):
    img = Image.fromarray(np.uint8(np.clip(arr, 0, 1) * 255))
    img = img.resize(size, Image.Resampling.BILINEAR)
    return np.asarray(img, dtype=np.float32).flatten() / 255.0


def extract_features(img):
    """
    Build several visual representations.

    We combine:
      1. normalized chart grayscale
      2. edge/shape representation
      3. horizontal/vertical structural summaries

    This is still visual retrieval, not a trading prediction model.
    """
    arr = make_structure_image(img, (96, 96))
    edges = gradient_features(arr)

    # Multi-scale visual representation.
    raw32 = downsample(arr, (32, 32))
    edge32 = downsample(edges / (edges.max() + 1e-6), (32, 32))

    # Horizontal and vertical density summaries.
    row_mean = arr.mean(axis=1)
    col_mean = arr.mean(axis=0)

    # Edge summaries capture where structure changes.
    row_edge = edges.mean(axis=1)
    col_edge = edges.mean(axis=0)

    feature = np.concatenate([
        raw32,
        edge32,
        row_mean,
        col_mean,
        row_edge,
        col_edge
    ]).astype(np.float32)

    norm = np.linalg.norm(feature)
    if norm:
        feature /= norm

    return feature


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
        json.dump(db, f, indent=2)


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
    data = uploaded_file.getvalue()
    return hashlib.sha256(data).hexdigest()


db = load_db()

# ------------------------------------------------------------
# Sidebar: add setup
# ------------------------------------------------------------

st.sidebar.header("➕ Add Historical Setup")

uploaded = st.sidebar.file_uploader(
    "Upload setup screenshot",
    type=["png", "jpg", "jpeg"],
    key="library_upload"
)

pair = st.sidebar.selectbox(
    "Market",
    ["XAUUSD", "USDCHF", "BTCUSD", "Other"]
)

timeframe = st.sidebar.selectbox(
    "Timeframe",
    ["1M", "5M", "15M", "30M", "1H", "4H", "Daily", "Other"]
)

direction = st.sidebar.selectbox(
    "Direction",
    ["Buy", "Sell", "Unknown / Don't care"]
)

result = st.sidebar.selectbox(
    "Backtest result",
    ["Win", "Loss", "Break-even", "Testing / Unknown"]
)

session = st.sidebar.selectbox(
    "Session",
    ["Asia / Tokyo", "London", "New York", "Overlap", "Unknown"]
)

notes = st.sidebar.text_area(
    "Optional notes",
    placeholder="What did you notice about this setup?"
)

if st.sidebar.button("💾 Save Setup"):
    if uploaded is None:
        st.sidebar.error("Upload a screenshot first.")
    else:
        try:
            content_hash = file_hash(uploaded)

            # Avoid accidental duplicate screenshots.
            duplicate = None
            for sid, item in db.items():
                if item.get("file_hash") == content_hash:
                    duplicate = sid
                    break

            if duplicate:
                st.sidebar.warning(f"This screenshot is already saved as {duplicate}.")
            else:
                img = Image.open(uploaded).convert("RGB")
                setup_id = new_id(db)
                image_path = save_image(img, setup_id)
                feature = extract_features(img)

                db[setup_id] = {
                    "market": pair,
                    "timeframe": timeframe,
                    "direction": direction,
                    "result": result,
                    "session": session,
                    "notes": notes,
                    "image": image_path,
                    "file_hash": content_hash,
                    "features": feature.tolist()
                }

                save_db(db)
                st.sidebar.success(f"Saved as {setup_id}")

        except Exception as e:
            st.sidebar.error(f"Could not save setup: {e}")

st.sidebar.markdown("---")
st.sidebar.metric("Saved setups", len(db))

# ------------------------------------------------------------
# Main: search library
# ------------------------------------------------------------

st.header("🔎 Find Similar Historical Setups")

query_file = st.file_uploader(
    "Upload the new chart/setup you want to compare",
    type=["png", "jpg", "jpeg"],
    key="query_upload"
)

top_n = st.slider(
    "Number of similar setups to show",
    min_value=3,
    max_value=12,
    value=6
)

if query_file:
    query_img = Image.open(query_file).convert("RGB")

    st.subheader("Current Setup")
    st.image(query_img, use_container_width=True)

    if not db:
        st.warning("Your setup library is empty. Save some historical setups first.")
    else:
        with st.spinner("Comparing candle/price-action structure..."):
            query_feature = extract_features(query_img)

            matches = []

            for sid, item in db.items():
                try:
                    old_feature = np.asarray(item["features"], dtype=np.float32)

                    # Cosine similarity because vectors are normalized.
                    score = float(np.dot(query_feature, old_feature))

                    matches.append({
                        "id": sid,
                        "score": score,
                        "market": item.get("market", "Unknown"),
                        "timeframe": item.get("timeframe", "Unknown"),
                        "direction": item.get("direction", "Unknown"),
                        "result": item.get("result", "Unknown"),
                        "session": item.get("session", "Unknown"),
                        "notes": item.get("notes", ""),
                        "image": item.get("image")
                    })

                except Exception:
                    continue

            matches.sort(key=lambda x: x["score"], reverse=True)
            matches = matches[:top_n]

        st.success(
            f"Found {len(matches)} historical setups with the closest visual "
            f"price-action structure."
        )

        st.info(
            "Similarity is a visual retrieval score — it is NOT a probability of "
            "winning and does not mean the new setup is valid."
        )

        # Display results.
        cols_per_row = 3

        for start in range(0, len(matches), cols_per_row):
            row = matches[start:start + cols_per_row]
            cols = st.columns(len(row))

            for col, match in zip(cols, row):
                with col:
                    st.markdown(f"### {match['id']}")

                    image_path = match["image"]
                    if image_path and os.path.exists(image_path):
                        st.image(
                            image_path,
                            use_container_width=True
                        )

                    st.markdown(
                        f"**Visual similarity:** "
                        f"`{match['score'] * 100:.1f}%`"
                    )

                    st.write(f"**Market:** {match['market']}")
                    st.write(f"**Timeframe:** {match['timeframe']}")
                    st.write(f"**Direction:** {match['direction']}")
                    st.write(f"**Result:** {match['result']}")
                    st.write(f"**Session:** {match['session']}")

                    if match["notes"]:
                        st.caption(match["notes"])

        # ----------------------------------------------------
        # Historical summary
        # ----------------------------------------------------

        st.markdown("---")
        st.header("📊 What the Similar Setups Tell You")

        known = [
            m for m in matches
            if m["result"] in ["Win", "Loss", "Break-even"]
        ]

        if known:
            wins = sum(m["result"] == "Win" for m in known)
            losses = sum(m["result"] == "Loss" for m in known)
            be = sum(m["result"] == "Break-even" for m in known)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Matched examples", len(known))
            c2.metric("Wins", wins)
            c3.metric("Losses", losses)
            c4.metric("Break-even", be)

            st.caption(
                "This is descriptive history from the retrieved examples only. "
                "It does not predict what the new trade will do."
            )
        else:
            st.write("No completed outcomes are recorded among the displayed matches.")

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
            st.caption(
                f"{item.get('market')} · "
                f"{item.get('timeframe')} · "
                f"{item.get('direction')} · "
                f"{item.get('result')}"
            )
else:
    st.write("No setups saved yet.")

st.markdown("---")
st.caption(
    "TEMEXY LIBRARY — Built for visual backtesting and pattern retrieval. "
    "Always inspect the actual chart before making a trading decision."
)
