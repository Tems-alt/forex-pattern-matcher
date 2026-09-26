import os
import pickle
import numpy as np
import torch
import streamlit as st
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

st.set_page_config(page_title="Forex Pattern Matcher", layout="wide")
st.title("📈 Forex Setup & Pattern Matcher")

STORAGE_DIR = "setup_library"
EMBEDDINGS_FILE = "embeddings.pkl"
os.makedirs(STORAGE_DIR, exist_ok=True)

@st.cache_resource
def load_clip_model():
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return model, processor

model, processor = load_clip_model()

def get_image_embedding(image):
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        features = model.get_image_features(**inputs)
    features = features / features.norm(p=2, dim=-1, keepdim=True)
    return features.cpu().numpy().flatten()

def load_database():
    if os.path.exists(EMBEDDINGS_FILE):
        with open(EMBEDDINGS_FILE, "rb") as f:
            return pickle.load(f)
    return {}

def save_database(db):
    with open(EMBEDDINGS_FILE, "wb") as f:
        pickle.dump(db, f)

db = load_database()

st.sidebar.header("📥 Save Past Setup")
uploaded_setup = st.sidebar.file_uploader("Upload Past Setup Screenshot", type=["png", "jpg", "jpeg"], key="upload_setup")
setup_label = st.sidebar.text_input("Setup Name / Pair (e.g. EURUSD Double Bottom)", key="setup_name")

if st.sidebar.button("Save Setup"):
    if uploaded_setup and setup_label:
        img = Image.open(uploaded_setup).convert("RGB")
        file_path = os.path.join(STORAGE_DIR, f"{setup_label}_{uploaded_setup.name}")
        img.save(file_path)
        
        vector = get_image_embedding(img)
        db[file_path] = {"label": setup_label, "vector": vector}
        save_database(db)
        
        st.sidebar.success(f"Saved '{setup_label}'!")
    else:
        st.sidebar.error("Please provide both an image and a label.")

st.sidebar.markdown("---")
st.sidebar.write(f"📁 **Total Saved Setups:** {len(db)}")

st.subheader("🔍 Match Live Chart")
live_chart = st.file_uploader("Upload Current Market Screenshot to Find Matches", type=["png", "jpg", "jpeg"])

if live_chart:
    col1, col2 = st.columns([1, 2])
    query_img = Image.open(live_chart).convert("RGB")
    
    with col1:
        st.image(query_img, caption="Live Chart Screenshot", use_container_width=True)
    
    if len(db) == 0:
        st.warning("Your library is empty! Please upload past setups in the sidebar first.")
    else:
        query_vector = get_image_embedding(query_img)
        scores = []
        
        for path, data in db.items():
            db_vector = data["vector"]
            similarity = float(np.dot(query_vector, db_vector))
            scores.append((similarity, path, data["label"]))
        
        scores.sort(key=lambda x: x[0], reverse=True)
        
        with col2:
            st.subheader("🎯 Matching Setups Found:")
            top_matches = scores[:3]
            match_cols = st.columns(len(top_matches))
            
            for idx, (score, img_path, label) in enumerate(top_matches):
                with match_cols[idx]:
                    match_img = Image.open(img_path)
                    match_percentage = round(score * 100, 1)
                    st.image(match_img, caption=f"{label}\nMatch: {match_percentage}%", use_container_width=True)
