import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from supabase import create_client, Client

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="My Streamlit App & Analysis Blog",
    page_icon="📊",
    layout="wide"
)

# Helper function to find secrets wherever they are located in TOML
def get_secret(key_name):
    if key_name in st.secrets:
        return st.secrets[key_name]
    # Check if nested inside auth or auth.google sections
    for section in ["auth", "auth.google"]:
        if section in st.secrets and key_name in st.secrets[section]:
            return st.secrets[section][key_name]
    return None

# Connect to Supabase
def get_supabase():
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_KEY")
    
    if not url or not key:
        st.error("⚠️ Could not find SUPABASE_URL or SUPABASE_KEY in Secrets. Check section formatting in TOML.")
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        st.error(f"⚠️ Supabase connection error: {e}")
        return None

# ==========================================
# 2. BLOG PAGE MODULE
# ==========================================
def render_blog_page():
    st.title("📈 Market Insights & Analysis Blog")
    st.caption("Browse analysis posts below, leave a comment, or hit like!")

    supabase = get_supabase()
    if not supabase:
        return

    # --- ADMIN SIDEBAR CONTROLS ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔑 Admin Panel")
    admin_password = st.sidebar.text_input("Admin Password", type="password")
    
    expected_password = get_secret("ADMIN_PASSWORD") or ""
    is_admin = admin_password != "" and admin_password == expected_password

    if is_admin:
        st.sidebar.success("Logged in as Admin")
        with st.expander("✍️ Create New Post (Admin Only)", expanded=True):
            with st.form("new_post_form", clear_on_submit=True):
                post_title = st.text_input("Post Title")
                post_content = st.text_area("Analysis Content (Markdown supported)", height=220)
                submit_post = st.form_submit_button("Publish Analysis")

                if submit_post:
                    if post_title and post_content:
                        try:
                            supabase.table("posts").insert({
                                "title": post_title,
                                "content": post_content
                            }).execute()
                            st.success("Post published successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error publishing post: {e}")
                    else:
                        st.warning("Please fill out both the title and content.")
    elif admin_password:
        st.sidebar.error("Incorrect Password")

    st.markdown("---")

    # --- FETCH POSTS FROM DATABASE ---
    try:
        posts_data = supabase.table("posts").select("*").order("created_at", desc=True).execute()
        posts = posts_data.data
    except Exception as e:
        st.error(f"Error fetching posts: {e}")
        return

    if not posts:
        st.info("No analysis posts published yet.")
        return

    # --- DISPLAY POSTS WITH LIKES AND COMMENTS ---
    for post in posts:
        post_id = post["id"]

        st.subheader(post["title"])
        st.caption(f"Published on: {post['created_at'][:10]}")
        st.markdown(post["content"])

        # Fetch likes count
        likes_data = supabase.table("likes").select("id", count="exact").eq("post_id", post_id).execute()
        like_count = likes_data.count or 0

        # Fetch comments
        comments_data = supabase.table("comments").select("*").eq("post_id", post_id).order("created_at", desc=False).execute()
        comments = comments_data.data

        # Like Button
        col_like, _ = st.columns([1, 4])
        with col_like:
            if st.button(f"❤️ Like ({like_count})", key=f"like_btn_{post_id}"):
                supabase.table("likes").insert({"post_id": post_id}).execute()
                st.rerun()

        # Display Comments
        st.markdown("##### 💬 Comments")
        if comments:
            for c in comments:
                st.markdown(f"**{c['author']}**: {c['comment']}")
        else:
            st.caption("No comments yet. Be the first to join the discussion!")

        # Add Comment Form
        with st.form(key=f"comment_form_{post_id}", clear_on_submit=True):
            author_name = st.text_input("Your Name", key=f"author_{post_id}")
            comment_text = st.text_area("Add a comment...", key=f"text_{post_id}", height=80)
            submit_comment = st.form_submit_button("Submit Comment")

            if submit_comment:
                if author_name and comment_text:
                    supabase.table("comments").insert({
                        "post_id": post_id,
                        "author": author_name,
                        "comment": comment_text
                    }).execute()
                    st.rerun()
                else:
                    st.warning("Please enter your name and a comment.")

        st.markdown("---")

# ==========================================
# 3. MAIN APP HOMEPAGE
# ==========================================
def render_main_page():
    st.title("📊 Main Dashboard")
    st.write("Welcome to your application dashboard! Place your main tools, metrics, and visualizers here.")
    
    df = pd.DataFrame({
        "Category": ["A", "B", "C", "D"],
        "Values": [23, 45, 56, 78]
    })
    fig = px.bar(df, x="Category", y="Values", title="Sample Dashboard Chart")
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 4. ROUTING & NAVIGATION
# ==========================================
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select Page:", ["Main Dashboard", "Analysis Blog"])

    if page == "Main Dashboard":
        render_main_page()
    elif page == "Analysis Blog":
        render_blog_page()

if __name__ == "__main__":
    main()
