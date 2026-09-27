import os
import sqlite3
import uuid
import math
from pathlib import Path
from datetime import datetime, date, time

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

# ------------------------------------------------------------------------------
# 1. DATABASE SETUP & INITIALIZATION
# ------------------------------------------------------------------------------
DB_FILE = "app_data.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Analysis posts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analysis (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        image_path TEXT,
        csv_path TEXT,
        likes INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Comments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id TEXT PRIMARY KEY,
        analysis_id TEXT NOT NULL,
        user_name TEXT NOT NULL,
        comment_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(analysis_id) REFERENCES analysis(id)
    );
    """)
    
    conn.commit()
    conn.close()

init_db()

# ------------------------------------------------------------------------------
# 2. STREAMLIT APP CONFIG & SESSION STATE
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Analytics & Creator Platform",
    page_icon="📊",
    layout="wide"
)

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# Ensure upload directory exists
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# ------------------------------------------------------------------------------
# 3. SIDEBAR NAVIGATION & AUTHENTICATION TOGGLE
# ------------------------------------------------------------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Analysis"])

st.sidebar.markdown("---")
st.sidebar.subheader("Creator Admin Toggle")
admin_key_input = st.sidebar.text_input("Enter Admin Secret Key", type="password")

if admin_key_input == "creator123":
    st.session_state.is_admin = True
    st.sidebar.success("Logged in as Admin/Creator")
else:
    st.session_state.is_admin = False
    if admin_key_input:
        st.sidebar.error("Invalid Secret Key")

# ------------------------------------------------------------------------------
# 4. PAGE 1: DASHBOARD
# ------------------------------------------------------------------------------
if page == "Dashboard":
    st.title("📊 Analytics Overview")
    st.write("Welcome to the analytics dashboard. Explore key metrics below.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Visitors", "12,450", "+5.2%")
    col2.metric("Engagement Rate", "8.4%", "+1.1%")
    col3.metric("Analysis Posts", "24", "+3")
    
    # Sample Plotly Chart
    st.subheader("Monthly Engagement")
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    views = [1200, 1900, 3000, 2500, 3200, 4100, 3900, 4800, 5100]
    
    fig = go.Figure(data=go.Scatter(x=months, y=views, mode='lines+markers', name='Page Views'))
    fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------------------
# 5. PAGE 2: ANALYSIS & COMMUNITY ENGAGEMENT
# ------------------------------------------------------------------------------
elif page == "Analysis":
    st.title("📈 Creator Analysis & Insights")
    st.write("In-depth analysis posts, data exports, and community discussions.")
    
    # Admin View: Posting Capability
    if st.session_state.is_admin:
        with st.expander("➕ Create New Analysis Post (Creator Only)", expanded=True):
            with st.form("new_analysis_form", clear_on_submit=True):
                post_title = st.text_input("Analysis Title")
                post_content = st.text_area("Analysis Content / Insights")
                uploaded_image = st.file_uploader("Upload Visual (Image)", type=["jpg", "jpeg", "png"])
                uploaded_csv = st.file_uploader("Attach Data Source (CSV)", type=["csv"])
                
                submitted = st.form_submit_button("Publish Post")
                
                if submitted:
                    if not post_title or not post_content:
                        st.error("Title and Content are required to publish.")
                    else:
                        img_path = None
                        csv_path = None
                        
                        if uploaded_image:
                            img_filename = f"{uuid.uuid4().hex}_{uploaded_image.name}"
                            img_path = str(UPLOAD_DIR / img_filename)
                            with open(img_path, "wb") as f:
                                f.write(uploaded_image.getbuffer())
                                
                        if uploaded_csv:
                            csv_filename = f"{uuid.uuid4().hex}_{uploaded_csv.name}"
                            csv_path = str(UPLOAD_DIR / csv_filename)
                            with open(csv_path, "wb") as f:
                                f.write(uploaded_csv.getbuffer())
                        
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO analysis (id, title, content, image_path, csv_path) VALUES (?, ?, ?, ?, ?)",
                            (uuid.uuid4().hex, post_title, post_content, img_path, csv_path)
                        )
                        conn.commit()
                        conn.close()
                        st.success("Analysis published successfully!")
                        st.rerun()

    st.markdown("---")
    
    # Display Existing Posts
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analysis ORDER BY created_at DESC")
    posts = cursor.fetchall()
    conn.close()
    
    if not posts:
        st.info("No analysis posts published yet.")
    else:
        for post in posts:
            post_id = post["id"]
            title = post["title"]
            content = post["content"]
            image_path = post["image_path"]
            csv_path = post["csv_path"]
            likes = post["likes"]
            created_at = post["created_at"]
            
            st.subheader(title)
            st.caption(f"Published on: {created_at}")
            st.write(content)
            
            # Display Image if available
            if image_path and os.path.exists(image_path):
                st.image(image_path, use_column_width=True)
                
            # Display and Download CSV if available
            if csv_path and os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                with st.expander("📊 Preview Attached Data Source"):
                    st.dataframe(df.head())
                    with open(csv_path, "rb") as f:
                        st.download_button(
                            label="Download Dataset (CSV)",
                            data=f,
                            file_name=os.path.basename(csv_path),
                            mime="text/csv",
                            key=f"dl_{post_id}"
                        )
            
            # Likes & Interaction Row
            col_like, col_space = st.columns([1, 5])
            with col_like:
                if st.button(f"❤️ {likes}", key=f"like_{post_id}"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE analysis SET likes = likes + 1 WHERE id = ?", (post_id,))
                    conn.commit()
                    conn.close()
                    st.rerun()
            
            # Comment Section
            st.markdown("#### Comments")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM comments WHERE analysis_id = ? ORDER BY created_at ASC", (post_id,))
            comments = cursor.fetchall()
            conn.close()
            
            if comments:
                for comment in comments:
                    st.markdown(f"**{comment['user_name']}**: {comment['comment_text']}")
                    st.caption(f"{comment['created_at']}")
            else:
                st.caption("No comments yet. Be the first to share your thoughts!")
                
            # Add Comment Form
            with st.form(key=f"comment_form_{post_id}", clear_on_submit=True):
                user_name = st.text_input("Name", value="Anonymous" if not st.session_state.is_admin else "Creator/Admin", key=f"name_{post_id}")
                comment_text = st.text_area("Add a comment...", key=f"text_{post_id}")
                submit_comment = st.form_submit_button("Post Comment")
                
                if submit_comment:
                    if comment_text.strip():
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO comments (id, analysis_id, user_name, comment_text) VALUES (?, ?, ?, ?)",
                            (uuid.uuid4().hex, post_id, user_name, comment_text)
                        )
                        conn.commit()
                        conn.close()
                        st.rerun()
                    else:
                        st.warning("Comment cannot be empty.")
                        
            st.markdown("---")
