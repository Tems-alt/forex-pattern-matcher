import os
import pickle
import numpy as np
import torch
import streamlit as st
import requests
from io import BytesIO
from PIL import Image, ImageOps, ImageEnhance
from transformers import CLIPProcessor, CLIPModel

st.set_page_config(page_title="Forex Strict Price Action Matcher", layout="wide")
st.title("🎯 Strict Forex Price Action & FVG Matcher")

STORAGE_DIR = "setup_library"
EMBEDDINGS_FILE = "embeddings.pkl"
os.makedirs(STORAGE_DIR, exist_ok=True)

@st.cache_resource
def load_clip_model():
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return model, processor

model, processor = load_clip_model()

def preprocess_chart_structure(image):
    """
    Strips away background color themes, UI elements, and converts chart
    into a high-contrast grayscale edge structure to focus ONLY on candlestick shapes.
    """
    # Crop central area (remove TradingView top/left UI bars)
    w, h = image.size
    crop_box = (int(w * 0.08), int(h * 0.12), int(w * 0.92), int(h * 0.88))
    cropped = image.crop(crop_box)
    
    # Convert to grayscale to remove green/red/dark-mode theme bias
    gray = cropped.convert("L")
    
    # Increase contrast to emphasize candlestick wicks and bodies
    enhancer = ImageEnhance.Contrast(gray)
    high_contrast = enhancer.enhance(2.0)
    
    # Convert back to RGB for CLIP model ingestion
    return high_contrast.convert("RGB")

def get_image_embedding(image):
    processed_img = preprocess_chart_structure(image)
    inputs = processor(images=processed_img, return_tensors="pt")
    
    with torch.no_grad():
        outputs = model.get_image_features(**inputs)
        if hasattr(outputs, 'image_embeds'):
            vector = outputs.image_embeds.cpu().numpy().flatten()
        elif hasattr(outputs, 'pooler_output'):
            vector = outputs.pooler_output.cpu().numpy().flatten()
        else:
            vector = outputs.cpu().numpy().flatten()
            
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector

def fetch_image_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGB")
    except Exception as e:
        st.error(f"Error loading image from URL: {e}")
        return None

def load_database():
    if os.path.exists(EMBEDDINGS_FILE):
        with open(EMBEDDINGS_FILE, "rb") as f:
            return pickle.load(f)
    return {}

def save_database(db):
    with open(EMBEDDINGS_FILE, "wb") as f:
        pickle.dump(db, f)

db = load_database()

# ---------------------------------------------------------
# SIDEBAR: SAVE MASTER SETUPS
# ---------------------------------------------------------
st.sidebar.header("📥 Save Master Model Setup")

input_type = st.sidebar.radio("Input Source", ["Upload File", "TradingView Image URL"])
img_to_save = None
filename_prefix = "uploaded"

if input_type == "Upload File":
    uploaded_setup = st.sidebar.file_uploader("Upload Setup Screenshot", type=["png", "jpg", "jpeg"], key="upload_setup")
    if uploaded_setup:
        img_to_save = Image.open(uploaded_setup).convert("RGB")
        filename_prefix = uploaded_setup.name
else:
    tv_url = st.sidebar.text_input("Paste TradingView Image URL")
    if tv_url:
        img_to_save = fetch_image_from_url(tv_url)
        filename_prefix = "tradingview_snapshot.png"

setup_label = st.sidebar.text_input("Setup Name / Pair (e.g. USDCHF_H1_FVG_Sweep)", key="setup_name")

st.sidebar.markdown("### 📋 Strict Model Requirements")
has_fvg = st.sidebar.checkbox("Fair Value Gap (FVG) Present", value=True)
has_sweep = st.sidebar.checkbox("Liquidity Sweep / Raid", value=True)
has_mss = st.sidebar.checkbox("Market Structure Shift (MSS)", value=True)

bias = st.sidebar.selectbox("Bias / Direction", ["Bearish (Sell)", "Bullish (Buy)"])
outcome = st.sidebar.selectbox("Historical Outcome", ["Win", "Loss", "Testing"])

if st.sidebar.button("Save Strict Setup to Database"):
    if img_to_save and setup_label:
        file_path = os.path.join(STORAGE_DIR, f"{setup_label}_{filename_prefix}")
        img_to_save.save(file_path)
        
        vector = get_image_embedding(img_to_save)
        db[file_path] = {
            "label": setup_label,
            "vector": vector,
            "bias": bias,
            "outcome": outcome,
            "rules": {"fvg": has_fvg, "sweep": has_sweep, "mss": has_mss}
        }
        save_database(db)
        
        st.sidebar.success(f"Saved Master Model '{setup_label}'!")
    else:
        st.sidebar.error("Please provide both an image/URL and a label.")

st.sidebar.markdown("---")
st.sidebar.write(f"📁 **Total Saved Models:** {len(db)}")

similarity_threshold = st.sidebar.slider("Strict Match Threshold (%)", min_value=85, max_value=99, value=94, step=1)

# ---------------------------------------------------------
# MAIN AREA: STRICT SCANNING
# ---------------------------------------------------------
st.subheader("🔍 Scan Live Chart (Strict Model Conformance)")

match_input_type = st.radio("Live Chart Input", ["Upload Screenshot", "Paste TradingView Link"], horizontal=True)
query_img = None

if match_input_type == "Upload Screenshot":
    live_chart = st.file_uploader("Upload Current Market Screenshot", type=["png", "jpg", "jpeg"])
    if live_chart:
        query_img = Image.open(live_chart).convert("RGB")
else:
    live_url = st.text_input("Paste Live TradingView Chart Image URL")
    if live_url:
        query_img = fetch_image_from_url(live_url)

if query_img:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image(query_img, caption="Live Chart Screenshot", use_container_width=True)
    
    if len(db) == 0:
        st.warning("Your playbook database is empty! Save your master setup models first.")
    else:
        query_vector = get_image_embedding(query_img)
        scores = []
        
        for path, data in db.items():
            db_vector = data["vector"]
            similarity = float(np.dot(query_vector, db_vector))
            scores.append((
                similarity,
                path,
                data["label"],
                data.get("bias", "N/A"),
                data.get("outcome", "N/A"),
                data.get("rules", {})
            ))
        
        scores.sort(key=lambda x: x[0], reverse=True)
        filtered_matches = [m for m in scores if (m[0] * 100) >= similarity_threshold]
        
        with col2:
            if not filtered_matches:
                st.error(f"❌ **INVALID SETUP — DOES NOT MEET YOUR MODEL RULES**")
                st.write(f"The candlestick structure on this live chart scores below your **{similarity_threshold}% strict threshold** (Top raw match was {round(scores[0][0]*100, 1)}%). Direction or FVG geometry does not match. **DO NOT ENTER THIS TRADE.**")
            else:
                top_matches = filtered_matches[:3]
                st.success(f"✅ **QUALIFIED MASTER SETUP DETECTED ({round(top_matches[0][0]*100, 1)}% Structural Match)**")
                
                rules = top_matches[0][5]
                st.markdown(f"**Required Model Rules Confirmed:**")
                st.write(f"- Fair Value Gap (FVG): {'✅ Yes' if rules.get('fvg') else '❌ No'}")
                st.write(f"- Liquidity Sweep: {'✅ Yes' if rules.get('sweep') else '❌ No'}")
                st.write(f"- Market Structure Shift: {'✅ Yes' if rules.get('mss') else '❌ No'}")
                
                st.markdown("---")
                match_cols = st.columns(len(top_matches))
                for idx, (score, img_path, label, m_bias, m_outcome, _) in enumerate(top_matches):
                    with match_cols[idx]:
                        match_img = Image.open(img_path)
                        st.image(
                            match_img,
                            caption=f"{label}\nMatch: {round(score * 100, 1)}%\nBias: {m_bias}\nOutcome: {m_outcome}",
                            use_container_width=True
                        )
