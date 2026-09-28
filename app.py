import os
import sqlite3
import uuid
import math
from pathlib import Path
from datetime import datetime, date, time
import calendar as pycalendar

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

import base64


# ============================================================
# TEMEXY TRADE JOURNAL
# A private, evidence-first trading journal.
# ============================================================

st.set_page_config(
    page_title="Temexy Trade Journal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ------------------------------------------------------------
# DESIGN SYSTEM
# ------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root{
  --bg:#06080B;
  --panel:#0C1015;
  --panel2:#10161E;
  --panel3:#151D27;
  --text:#F5F8FC;
  --muted:#8C9AAA;
  --muted2:#5F6D7C;
  --line:rgba(255,255,255,.075);
  --line2:rgba(255,255,255,.14);
  --blue:#3D9BFF;
  --blue2:#74BCFF;
  --blue3:#1E6FD1;
  --green:#38D39F;
  --red:#F15B68;
  --white:#FFFFFF;
}
*{box-sizing:border-box}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{
  background:
    radial-gradient(circle at 50% -20%,rgba(61,155,255,.10),transparent 34%),
    radial-gradient(circle at 100% 35%,rgba(61,155,255,.055),transparent 25%),
    #06080B;
  color:var(--text);
}
[data-testid="stSidebar"]{display:none}
[data-testid="stHeader"]{background:transparent}
.block-container{max-width:1500px;padding:1rem 2rem 4rem}
h1,h2,h3{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.035em;color:#F5F8FC!important}
h1{font-size:2.25rem!important}
h2{font-size:1.55rem!important}
h3{font-size:1.08rem!important}
p,label,.stCaption{color:#9EABB9}

/* Top application shell */
.top-shell{
  position:sticky;top:8px;z-index:999;
  margin-bottom:12px;
  background:rgba(8,11,15,.90);
  border:1px solid var(--line);
  border-radius:18px;
  box-shadow:0 18px 60px rgba(0,0,0,.34);
  backdrop-filter:blur(22px);
}
.top-main{display:flex;align-items:center;gap:15px;padding:12px 14px}
.brand{display:flex;align-items:center;gap:10px;min-width:185px}
.brand-mark{
  width:40px;height:40px;border-radius:11px;display:grid;place-items:center;
  background:linear-gradient(145deg,#4EA1FF,#2369B5);
  box-shadow:0 8px 28px rgba(61,155,255,.18)
}
.brand-mark svg{width:25px;height:25px}
.brand-name{font-family:'Space Grotesk';font-size:17px;font-weight:700;letter-spacing:.13em}
.brand-tag{font-size:8px;letter-spacing:.22em;color:#647385;font-weight:700}
.user-chip{
  margin-left:auto;border-left:1px solid var(--line);padding-left:15px;
  color:#748394;font-size:10px;white-space:nowrap
}
.user-chip b{color:#EAF2FA}

/* Navigation — neutral, blue active state, not a row of orange pills */
.nav-scroll{display:flex;gap:6px;padding:0 13px 11px;overflow-x:auto;scrollbar-width:none}
.nav-scroll::-webkit-scrollbar{display:none}
div[data-testid="stHorizontalBlock"] .stButton>button{
  min-height:38px;font-size:11px;padding:0 11px;border-radius:9px;
  transition:all .18s ease;white-space:nowrap;
  letter-spacing:.01em;
}
div[data-testid="stHorizontalBlock"] button[data-testid="stBaseButton-secondary"]{
  background:#0D1218!important;
  color:#AAB6C4!important;
  border:1px solid rgba(255,255,255,.065)!important;
  box-shadow:none!important;
}
div[data-testid="stHorizontalBlock"] button[data-testid="stBaseButton-secondary"]:hover{
  background:#121A23!important;color:#EAF2FA!important;
  border-color:rgba(78,161,255,.38)!important;
  transform:translateY(-1px);
}
div[data-testid="stHorizontalBlock"] button[data-testid="stBaseButton-primary"]{
  background:#EAF2FA!important;color:#071019!important;
  border:1px solid #EAF2FA!important;
  box-shadow:0 7px 20px rgba(234,242,250,.08)!important;
}

/* General controls */
.stButton>button,.stFormSubmitButton>button{
  min-height:42px;border-radius:10px!important;
  background:#10161E!important;color:#DCE7F2!important;
  border:1px solid rgba(255,255,255,.09)!important;
  font-weight:700!important;
  transition:all .18s ease!important;
}
.stButton>button:hover,.stFormSubmitButton>button:hover{
  background:#151F2A!important;border-color:rgba(78,161,255,.45)!important;
  color:#FFFFFF!important;transform:translateY(-1px);
}
.stButton>button:active,.stFormSubmitButton>button:active{transform:scale(.985)}
button[data-testid="stBaseButton-primary"]{
  background:#4EA1FF!important;color:#04101C!important;
  border-color:#4EA1FF!important;
  box-shadow:0 8px 24px rgba(61,155,255,.16)!important;
}
button[data-testid="stBaseButton-primary"]:hover{
  background:#74BCFF!important;border-color:#74BCFF!important;color:#04101C!important;
}
.stTextInput input,.stNumberInput input,.stTextArea textarea,
.stSelectbox div[data-baseweb="select"]>div,.stDateInput input,.stTimeInput input{
  background:#0C1117!important;color:#F0F5FA!important;
  border:1px solid rgba(255,255,255,.085)!important;border-radius:9px!important
}
[data-testid="stExpander"],[data-testid="stForm"]{
  border:1px solid var(--line);border-radius:15px;background:rgba(12,16,21,.74)
}
[data-testid="stForm"]{padding:8px}
[data-testid="stFileUploaderDropzone"]{
  background:#0B1016!important;border:1px dashed rgba(78,161,255,.25)!important;border-radius:12px!important
}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:13px;overflow:hidden}
hr{border-color:var(--line)!important}
footer{visibility:hidden}
a{color:#74BCFF!important}

/* Hero */
.hero{
  position:relative;overflow:hidden;
  padding:25px 27px;margin:5px 0 20px;
  border:1px solid var(--line);border-radius:20px;
  background:
    radial-gradient(circle at 86% 10%,rgba(61,155,255,.10),transparent 24%),
    linear-gradient(145deg,#0E141B,#0A0E13);
  box-shadow:0 18px 55px rgba(0,0,0,.22)
}
.hero:after{
  content:'';position:absolute;width:310px;height:310px;right:-155px;top:-155px;
  border:1px solid rgba(78,161,255,.10);border-radius:50%;
}
.hero-kicker{color:#74BCFF;font-size:9px;font-weight:800;letter-spacing:.20em;text-transform:uppercase}
.hero-title{font-family:'Space Grotesk';font-size:31px;font-weight:700;margin:5px 0;color:#F5F8FC}
.hero-sub{color:#8F9EAE;font-size:13px;max-width:920px;line-height:1.6}

/* Metric and content cards */
[data-testid="metric-container"]{
  background:linear-gradient(145deg,#10161D,#0B1015);
  border:1px solid var(--line);padding:14px 16px;border-radius:14px;
  box-shadow:0 10px 32px rgba(0,0,0,.17)
}
[data-testid="stMetricLabel"]{color:#7E8D9D!important;font-size:10px!important;text-transform:uppercase;letter-spacing:.07em}
[data-testid="stMetricValue"]{color:#F5F8FC!important;font-family:'Space Grotesk'}
.card{
  background:linear-gradient(145deg,#10161D,#0B1015);
  border:1px solid var(--line);border-radius:15px;padding:17px;
  box-shadow:0 12px 35px rgba(0,0,0,.16);height:100%
}
.card-title{font-family:'Space Grotesk';font-weight:700;color:#DDE7F1;font-size:13px;margin-bottom:6px}
.card-value{font-family:'Space Grotesk';font-size:25px;font-weight:700;color:#F5F8FC}
.card-sub{font-size:10px;color:#758496;margin-top:4px;line-height:1.5}
.section-title{
  display:flex;align-items:center;gap:8px;margin:22px 0 10px;
  font-family:'Space Grotesk';font-size:14px;font-weight:700;color:#DCE7F2
}
.section-dot{width:6px;height:6px;border-radius:50%;background:var(--blue);box-shadow:0 0 13px rgba(61,155,255,.65)}
.small-muted{color:#6E7C8B;font-size:10px}
.positive{color:var(--green)!important}.negative{color:var(--red)!important}.gold{color:#DCE7F2!important}

/* Analysis posts — meant to be READ, so bigger and higher contrast
   than the dense trade tables elsewhere in the app */
.post-title{
  font-family:'Space Grotesk';font-weight:700;font-size:23px;
  color:#FFFFFF;line-height:1.35;margin-bottom:3px
}
.post-meta{font-size:12px;color:#87ADDE;font-weight:600;margin-bottom:14px}
.post-body{
  font-size:16px;line-height:1.8;color:#EFF4FA;font-weight:500;
  white-space:pre-wrap;word-wrap:break-word
}
@media(max-width:560px){
  .post-title{font-size:20px}
  .post-meta{font-size:11px}
  .post-body{font-size:15.5px;line-height:1.75}
}

/* Creator card */
.creator-card{
  display:flex;gap:16px;align-items:center;padding:15px;
  border-radius:16px;border:1px solid rgba(78,161,255,.16);
  background:linear-gradient(145deg,#0E151D,#0A0F15);
}
.creator-photo{
  width:84px;height:84px;border-radius:15px;object-fit:cover;
  border:1px solid rgba(255,255,255,.10);
  box-shadow:0 8px 26px rgba(0,0,0,.30)
}
.creator-label{font-size:9px;letter-spacing:.17em;text-transform:uppercase;color:#5F8FBE;font-weight:800}
.creator-name{font-family:'Space Grotesk';font-size:17px;font-weight:700;color:#F5F8FC;margin-top:2px}
.creator-text{font-size:11px;line-height:1.5;color:#8492A1;margin-top:3px}

/* Trade rows */
.trade-row{
  display:grid;grid-template-columns:70px 1.35fr .8fr .7fr .75fr .8fr;
  gap:12px;align-items:center;padding:12px 13px;
  border-bottom:1px solid var(--line);font-size:11px
}
.trade-row:first-child{border-top:1px solid var(--line)}
.trade-row:hover{background:rgba(78,161,255,.025)}
.pill{
  display:inline-flex;align-items:center;justify-content:center;
  border:1px solid var(--line);border-radius:999px;padding:4px 8px;
  font-size:9px;font-weight:700;background:#10161D
}
.pill-win{color:var(--green);border-color:rgba(56,211,159,.20);background:rgba(56,211,159,.05)}
.pill-loss{color:var(--red);border-color:rgba(241,91,104,.20);background:rgba(241,91,104,.05)}
.pill-be{color:#B9C7D6;border-color:rgba(185,199,214,.18);background:rgba(185,199,214,.04)}

/* Trading calendar */
.calendar-wrap{border:1px solid var(--line);border-radius:16px;overflow:hidden;background:#0B1015;box-shadow:0 14px 38px rgba(0,0,0,.18)}
.calendar-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr))}
.cal-head{padding:10px 8px;text-align:center;font-size:9px;letter-spacing:.12em;color:#6F7F90;background:#0E141B;border-right:1px solid var(--line);border-bottom:1px solid var(--line);font-weight:800}
.cal-cell{min-height:92px;padding:9px;border-right:1px solid var(--line);border-bottom:1px solid var(--line);background:#0C1117;position:relative}
.cal-cell:nth-child(7n){border-right:0}
.cal-empty{background:#080C11}
.cal-day{font-family:'Space Grotesk';font-size:12px;font-weight:700;color:#DCE7F2}
.cal-pnl{margin-top:13px;font-family:'Space Grotesk';font-size:12px;font-weight:700}
.cal-r{margin-top:4px;font-size:9px;color:#7D8B9A}
.cal-no-trade{margin-top:25px;font-size:9px;color:#4F5D6C}
.cal-profit{background:linear-gradient(145deg,rgba(56,211,159,.10),rgba(12,17,23,.95))}
.cal-profit .cal-pnl{color:var(--green)}
.cal-loss{background:linear-gradient(145deg,rgba(241,91,104,.10),rgba(12,17,23,.95))}
.cal-loss .cal-pnl{color:var(--red)}
.cal-flat .cal-pnl{color:#AEBBCC}
@media(max-width:700px){
  .cal-cell{min-height:74px;padding:6px}
  .cal-pnl{font-size:10px;margin-top:8px}
  .cal-r{font-size:8px}
  .cal-no-trade{margin-top:17px}
  .cal-head{font-size:7px;padding:8px 3px}
}

/* Responsive */
@media(max-width:900px){
  .block-container{padding:.65rem .75rem 3rem}
  .top-main{gap:9px;padding:9px}
  .brand{min-width:auto}
  .user-chip{display:none}
  .hero{padding:21px 18px;border-radius:17px}
  .hero-title{font-size:25px}
  h1{font-size:1.8rem!important}
  .trade-row{grid-template-columns:58px 1fr .7fr .75fr;font-size:10px}
  .trade-row .optional{display:none}
  .creator-photo{width:70px;height:70px}
}
@media(max-width:560px){
  .block-container{padding:.45rem .45rem 2.5rem}
  .brand-name{font-size:15px}.brand-mark{width:36px;height:36px}
  .nav-scroll{padding:0 7px 8px}
  .hero{margin-bottom:13px;padding:18px 15px}
  .hero-title{font-size:22px}
  .hero-sub{font-size:11px}
  [data-testid="metric-container"]{padding:11px;border-radius:12px}
  .card{padding:13px;border-radius:13px}
  .trade-row{grid-template-columns:52px 1fr .7fr}
  .trade-row .hide-mobile{display:none}
  .creator-card{padding:12px;gap:12px}
  .creator-photo{width:60px;height:60px}
}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------
# STORAGE
# ------------------------------------------------------------
BASE = Path("trade_journal_data")
IMG = BASE / "images"
DB = BASE / "trades.db"
IMG.mkdir(parents=True, exist_ok=True)

# Creator photo — loaded from an actual file next to app.py, not a giant
# inline base64 string (fragile to hand-edit and easy to corrupt silently).
# Put a file named creator.jpg (or .png) alongside app.py to show it.
CREATOR_IMAGE_CANDIDATES = [Path("creator.jpg"), Path("creator.jpeg"), Path("creator.png")]


def creator_image_src():
    for p in CREATOR_IMAGE_CANDIDATES:
        if p.exists():
            try:
                data = p.read_bytes()
                mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
                b64 = base64.b64encode(data).decode()
                return f"data:{mime};base64,{b64}"
            except Exception:
                continue
    return None



def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    c = conn()
    c.execute("""CREATE TABLE IF NOT EXISTS trades(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        trade_date TEXT,
        trade_time TEXT,
        market TEXT,
        direction TEXT,
        timeframe TEXT,
        session TEXT,
        setup_name TEXT,
        setup_tags TEXT,
        htf_bias TEXT,
        entry REAL,
        stop_loss REAL,
        take_profit REAL,
        exit_price REAL,
        planned_rr REAL,
        actual_r REAL,
        pnl_money REAL,
        risk_percent REAL,
        risk_money REAL,
        result TEXT,
        confidence INTEGER,
        rule_adherence INTEGER,
        setup_quality INTEGER,
        news_event TEXT,
        market_context TEXT,
        reason TEXT,
        execution TEXT,
        emotion_before TEXT,
        emotion_during TEXT,
        emotion_after TEXT,
        mistake TEXT,
        lesson TEXT,
        what_went_well TEXT,
        what_to_change TEXT,
        screenshot_before TEXT,
        screenshot_setup TEXT,
        screenshot_after TEXT,
        created_at TEXT
    )""")
    for col, typ in [
        ("user_id", "TEXT"),
        ("emotion_before", "TEXT"),
        ("emotion_during", "TEXT"),
        ("emotion_after", "TEXT"),
    ]:
        try:
            c.execute(f"ALTER TABLE trades ADD COLUMN {col} {typ}")
        except sqlite3.OperationalError:
            pass

    c.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id TEXT PRIMARY KEY,
        email TEXT,
        name TEXT,
        first_seen TEXT,
        last_seen TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS preferences(
        user_id TEXT PRIMARY KEY,
        starting_balance REAL DEFAULT 0,
        currency TEXT DEFAULT 'USD',
        monthly_goal REAL DEFAULT 0,
        max_risk REAL DEFAULT 1,
        default_rr REAL DEFAULT 2
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS blog_posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        image TEXT,
        author_name TEXT,
        author_id TEXT,
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS blog_likes(
        post_id INTEGER,
        user_id TEXT,
        PRIMARY KEY(post_id, user_id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS blog_comments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_id TEXT,
        user_name TEXT,
        comment TEXT,
        created_at TEXT
    )""")
    c.commit()
    c.close()


init()


def touch_user(user_id, email, name):
    c = conn()
    now = datetime.now().isoformat()
    row = c.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,)).fetchone()
    if row:
        c.execute(
            "UPDATE users SET last_seen=?,email=?,name=? WHERE user_id=?",
            (now, email, name, user_id),
        )
    else:
        c.execute(
            "INSERT INTO users(user_id,email,name,first_seen,last_seen) VALUES(?,?,?,?,?)",
            (user_id, email, name, now, now),
        )
    c.commit()
    c.close()


def get_preferences(user_id):
    c = conn()
    row = c.execute("SELECT * FROM preferences WHERE user_id=?", (user_id,)).fetchone()
    c.close()
    return dict(row) if row else {
        "starting_balance": 0.0,
        "currency": "USD",
        "monthly_goal": 0.0,
        "max_risk": 1.0,
        "default_rr": 2.0,
    }


def save_preferences(user_id, starting_balance, currency, monthly_goal, max_risk, default_rr):
    c = conn()
    c.execute("""INSERT INTO preferences(user_id,starting_balance,currency,monthly_goal,max_risk,default_rr)
                 VALUES(?,?,?,?,?,?)
                 ON CONFLICT(user_id) DO UPDATE SET
                 starting_balance=excluded.starting_balance,
                 currency=excluded.currency,
                 monthly_goal=excluded.monthly_goal,
                 max_risk=excluded.max_risk,
                 default_rr=excluded.default_rr""",
              (user_id, starting_balance, currency, monthly_goal, max_risk, default_rr))
    c.commit()
    c.close()


def all_users():
    c = conn()
    rows = [dict(r) for r in c.execute("SELECT * FROM users ORDER BY last_seen DESC")]
    c.close()
    return rows


def total_trade_count():
    c = conn()
    n = c.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    c.close()
    return n


def save_blog_image(uploaded):
    if not uploaded:
        return None
    udir = BASE / "blog_images"
    udir.mkdir(parents=True, exist_ok=True)
    p = udir / f"{uuid.uuid4().hex[:10]}.png"
    Image.open(uploaded).convert("RGB").save(p, "PNG")
    return str(p)


def add_post(title, content, image, author_name, author_id):
    c = conn()
    c.execute(
        "INSERT INTO blog_posts(title,content,image,author_name,author_id,created_at) VALUES(?,?,?,?,?,?)",
        (title, content, image, author_name, author_id, datetime.now().isoformat()),
    )
    c.commit()
    c.close()


def get_posts():
    c = conn()
    rows = [dict(r) for r in c.execute("SELECT * FROM blog_posts ORDER BY created_at DESC")]
    c.close()
    return rows


def delete_post(post_id):
    c = conn()
    row = c.execute("SELECT image FROM blog_posts WHERE id=?", (post_id,)).fetchone()
    if row and row["image"]:
        try:
            Path(row["image"]).unlink(missing_ok=True)
        except Exception:
            pass
    c.execute("DELETE FROM blog_posts WHERE id=?", (post_id,))
    c.execute("DELETE FROM blog_likes WHERE post_id=?", (post_id,))
    c.execute("DELETE FROM blog_comments WHERE post_id=?", (post_id,))
    c.commit()
    c.close()


def toggle_like(post_id, user_id):
    c = conn()
    row = c.execute(
        "SELECT 1 FROM blog_likes WHERE post_id=? AND user_id=?", (post_id, user_id)
    ).fetchone()
    if row:
        c.execute("DELETE FROM blog_likes WHERE post_id=? AND user_id=?", (post_id, user_id))
    else:
        c.execute("INSERT INTO blog_likes(post_id,user_id) VALUES(?,?)", (post_id, user_id))
    c.commit()
    c.close()


def user_has_liked(post_id, user_id):
    c = conn()
    row = c.execute(
        "SELECT 1 FROM blog_likes WHERE post_id=? AND user_id=?", (post_id, user_id)
    ).fetchone()
    c.close()
    return row is not None


def get_like_count(post_id):
    c = conn()
    n = c.execute("SELECT COUNT(*) FROM blog_likes WHERE post_id=?", (post_id,)).fetchone()[0]
    c.close()
    return n


def add_comment(post_id, user_id, user_name, text):
    c = conn()
    c.execute(
        "INSERT INTO blog_comments(post_id,user_id,user_name,comment,created_at) VALUES(?,?,?,?,?)",
        (post_id, user_id, user_name, text, datetime.now().isoformat()),
    )
    c.commit()
    c.close()


def get_comments(post_id):
    c = conn()
    rows = [dict(r) for r in c.execute(
        "SELECT * FROM blog_comments WHERE post_id=? ORDER BY created_at ASC", (post_id,)
    )]
    c.close()
    return rows


def delete_comment(comment_id):
    c = conn()
    c.execute("DELETE FROM blog_comments WHERE id=?", (comment_id,))
    c.commit()
    c.close()


def trades(user_id):
    c = conn()
    rows = [dict(r) for r in c.execute(
        "SELECT * FROM trades WHERE user_id=? ORDER BY trade_date DESC,trade_time DESC,id DESC",
        (user_id,),
    )]
    c.close()
    return rows


def get_trade(tid, user_id):
    c = conn()
    row = c.execute(
        "SELECT * FROM trades WHERE id=? AND user_id=?", (tid, user_id)
    ).fetchone()
    c.close()
    return dict(row) if row else None


def add_trade(data):
    c = conn()
    cols = list(data)
    placeholders = ",".join(["?"] * len(cols))
    c.execute(
        f"INSERT INTO trades({','.join(cols)}) VALUES({placeholders})",
        [data[x] for x in cols],
    )
    c.commit()
    trade_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    c.close()
    return trade_id


def remove_trade(tid, user_id):
    t = get_trade(tid, user_id)
    if not t:
        return
    for key in ("screenshot_before", "screenshot_setup", "screenshot_after"):
        p = t.get(key)
        if p:
            try:
                Path(p).unlink(missing_ok=True)
            except Exception:
                pass
    c = conn()
    c.execute("DELETE FROM trades WHERE id=? AND user_id=?", (tid, user_id))
    c.commit()
    c.close()


def saveimg(uploaded, prefix, user_id):
    if not uploaded:
        return None
    udir = IMG / user_id
    udir.mkdir(parents=True, exist_ok=True)
    p = udir / f"{prefix}_{uuid.uuid4().hex[:8]}.png"
    Image.open(uploaded).convert("RGB").save(p, "PNG")
    return str(p)


def money(x, currency="USD"):
    try:
        symbol = {"USD": "$", "NGN": "₦", "GBP": "£", "EUR": "€"}.get(currency, currency + " ")
        return f"{symbol}{float(x):,.2f}"
    except Exception:
        return "—"


def num(x):
    try:
        return f"{float(x):.2f}"
    except Exception:
        return "—"


def hero(kicker, title, sub):
    st.markdown(
        f"""<div class="hero">
        <div class="hero-kicker">{kicker}</div>
        <div class="hero-title">{title}</div>
        <div class="hero-sub">{sub}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def section(title):
    st.markdown(
        f'<div class="section-title"><span class="section-dot"></span>{title}</div>',
        unsafe_allow_html=True,
    )


def result_pill(result):
    cls = {
        "Win": "pill-win",
        "Loss": "pill-loss",
        "Break-even": "pill-be",
        "Partial / Mixed": "pill-be",
    }.get(result, "")
    return f'<span class="pill {cls}">{result}</span>'



# ------------------------------------------------------------
# PREMIUM CHARTS
# ------------------------------------------------------------
def premium_line_chart(df, x_col, y_cols, labels=None, height=310, zero_line=False):
    fig = go.Figure()
    labels = labels or y_cols
    blue_shades = ["#4EA1FF", "#8CC8FF", "#DCEEFF"]
    for i, (col, label) in enumerate(zip(y_cols, labels)):
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[col],
            mode="lines",
            name=label,
            line=dict(
                color=blue_shades[i % len(blue_shades)],
                width=2.5,
                shape="spline",
            ),
            fill="tozeroy" if i == 0 else None,
            fillcolor="rgba(78,161,255,.08)" if i == 0 else None,
            hovertemplate=f"<b>{label}</b><br>%{{x}}<br>%{{y:.2f}}<extra></extra>",
        ))
    if zero_line:
        fig.add_hline(y=0, line_width=1, line_dash="dot", line_color="rgba(255,255,255,.18)")
    fig.update_layout(
        height=height,
        margin=dict(l=8,r=8,t=18,b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0B0D11",
        font=dict(family="DM Sans", color="#EAF2FA", size=11),
        hovermode="x unified",
        legend=dict(
            orientation="h", y=1.08, x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=10, color="#AEBBCC"),
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            color="#77869A",
            linecolor="rgba(255,255,255,.07)",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,.055)",
            zeroline=False,
            color="#77869A",
        ),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})


def premium_bar_chart(series, title="", height=260, value_suffix="R"):
    s = pd.Series(series)
    fig = go.Figure(go.Bar(
        x=s.index.astype(str),
        y=s.values,
        marker=dict(
            color=["#4EA1FF" if v >= 0 else "#F15B68" for v in s.values],
            line=dict(width=0),
        ),
        hovertemplate="%{x}<br><b>%{y:.2f}" + value_suffix + "</b><extra></extra>",
    ))
    fig.update_layout(
        height=height,
        margin=dict(l=8,r=8,t=30,b=8),
        title=dict(text=title, font=dict(size=12, color="#DCE7F2")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0B0D11",
        font=dict(family="DM Sans", color="#EAF2FA"),
        xaxis=dict(showgrid=False, color="#77869A"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,.055)", color="#77869A"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})


# ------------------------------------------------------------
# AUTH
# ------------------------------------------------------------
if st.query_params.get("policy") == "1":
    st.title("Temexy Trade Journal — Privacy Policy")
    st.caption("Last updated: September 27, 2026")
    st.markdown("""
**What we collect**
- Your Google name, email and account identifier for sign-in and account separation.
- Trade data you enter and screenshots you choose to upload.

**What we don't do**
- We don't sell your journal data or show advertising.
- Your account is separated from other users at the database level.

**Where data lives**
Your journal and screenshots are stored in this app's database/filesystem. Keep your own backups of important records.
""")
    st.stop()

try:
    signed_in = st.user.is_logged_in
except Exception:
    st.error(
        "Google sign-in isn't active on this deployment. Check the [auth] and [auth.google] "
        "secrets in Streamlit Cloud and reboot the app."
    )
    st.stop()

if not signed_in:
    st.markdown(
        """<div class="hero" style="max-width:560px;margin:9vh auto 0;text-align:center">
        <div class="hero-kicker">TEMEXY • PRIVATE JOURNAL</div>
        <div class="hero-title" style="font-size:27px">Your trading command center</div>
        <div class="hero-sub" style="margin:auto">Journal every trade, measure your process, understand your risk and build evidence around your execution.</div>
        </div>""",
        unsafe_allow_html=True,
    )
    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        if st.button("Continue with Google", use_container_width=True, type="primary"):
            st.login("google")
    st.stop()

USER_ID = st.user.sub
USER_EMAIL = st.user.get("email") or ""
USER_NAME = st.user.get("name") or USER_EMAIL or "Trader"
touch_user(USER_ID, USER_EMAIL, USER_NAME)
ADMIN_EMAILS = {"e.fabiyi0583@miva.edu.ng"}
IS_ADMIN = USER_EMAIL in ADMIN_EMAILS
T = trades(USER_ID)
PREF = get_preferences(USER_ID)


# ------------------------------------------------------------
# NAVIGATION
# ------------------------------------------------------------
PAGE_MAP = {
    "dashboard": "Dashboard",
    "insights": "Analysis",
    "journal": "Journal",
    "calendar": "Calendar",
    "new-trade": "New Trade",
    "detail": "Trade Detail",
    "analytics": "Analytics",
    "risk": "Risk Lab",
    "settings": "Settings",
}
NAV_ITEMS = list(PAGE_MAP.items()) + [("logout", "Log out")]

if "page" not in st.session_state:
    st.session_state.page = "dashboard"
if st.session_state.page not in PAGE_MAP:
    st.session_state.page = "dashboard"

current_key = st.session_state.page

wins = sum(x["result"] == "Win" for x in T) if T else 0
net_r = sum(float(x["actual_r"] or 0) for x in T) if T else 0
win_rate = (wins / len(T) * 100) if T else 0


brand_html = f"""
<div class="top-shell">
  <div class="top-main">
    <div class="brand">
      <div class="brand-mark">
        <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M7 29V16L13 22L19 13L25 19L33 7" stroke="#171311" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M12 9V29M8.5 13H15.5M8.5 19H15.5" stroke="#F8E5C2" stroke-width="2.2" stroke-linecap="round"/>
        </svg>
      </div>
      <div><div class="brand-name">TEMEXY</div><div class="brand-tag">TRADE JOURNAL</div></div>
    </div>
    <div class="user-chip">TRADES <b>{len(T)}</b> &nbsp; • &nbsp; NET <b>{net_r:+.2f}R</b> &nbsp; • &nbsp; {USER_NAME}</div>
  </div>
</div>
"""
st.markdown(brand_html, unsafe_allow_html=True)

nav_cols = st.columns(len(NAV_ITEMS))
for col, (key, label) in zip(nav_cols, NAV_ITEMS):
    with col:
        if st.button(
            label,
            key=f"nav_{key}",
            use_container_width=True,
            type="primary" if key == current_key else "secondary",
        ):
            if key == "logout":
                st.logout()
            else:
                st.session_state.page = key
                st.rerun()


# ------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------
if current_key == "dashboard":
    hero(
        "TEMEXY • PERFORMANCE CENTER",
        "Your trading command center.",
        "A clean, evidence-first workspace for journaling trades, reviewing execution, measuring risk and building consistency.",
    )

    c1, c2 = st.columns([1.65, 1])
    with c2:
        _photo_src = creator_image_src()
        _photo_html = (
            f'<img class="creator-photo" src="{_photo_src}" />'
            if _photo_src else
            '<div class="creator-photo" style="display:grid;place-items:center;'
            'background:linear-gradient(145deg,#4EA1FF,#2369B5);'
            'font-family:\'Space Grotesk\';font-weight:700;font-size:22px;color:#04101C">FE</div>'
        )
        st.markdown(
            f"""<div class="creator-card">
              {_photo_html}
              <div>
                <div class="creator-label">Created by</div>
                <div class="creator-name">Fabiyi Emmanuel</div>
                <div class="creator-text">Creator of Temexy Journal — built to turn every trade into measurable feedback.</div>
              </div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c1:
        st.markdown(
            """<div class="card">
              <div class="card-title">TEMEXY OS</div>
              <div class="card-value">Process over noise.</div>
              <div class="card-sub">Log the decision. Measure the execution. Review the evidence. Improve the process.</div>
            </div>""",
            unsafe_allow_html=True,
        )

    if not T:
        section("Start here")
        a, b, c = st.columns(3)
        with a:
            st.markdown('<div class="card"><div class="card-title">01 · Log the trade</div><div class="card-value">Journal</div><div class="card-sub">Capture the setup before memory changes the story.</div></div>', unsafe_allow_html=True)
        with b:
            st.markdown('<div class="card"><div class="card-title">02 · Measure it</div><div class="card-value">Analytics</div><div class="card-sub">Find patterns across markets, sessions and setups.</div></div>', unsafe_allow_html=True)
        with c:
            st.markdown('<div class="card"><div class="card-title">03 · Protect it</div><div class="card-value">Risk Lab</div><div class="card-sub">Model risk, drawdown and compounding before trading.</div></div>', unsafe_allow_html=True)
        st.markdown("")
        if st.button("＋ Log your first trade", type="primary"):
            st.session_state.page = "new-trade"
            st.rerun()
    else:
        d = pd.DataFrame(T)
        d["actual_r"] = pd.to_numeric(d["actual_r"], errors="coerce").fillna(0)
        d["pnl_money"] = pd.to_numeric(d["pnl_money"], errors="coerce").fillna(0)
        d["rule_adherence"] = pd.to_numeric(d["rule_adherence"], errors="coerce")
        d["setup_quality"] = pd.to_numeric(d["setup_quality"], errors="coerce")
        d["confidence"] = pd.to_numeric(d["confidence"], errors="coerce")

        gross_win = d.loc[d.actual_r > 0, "actual_r"].sum()
        gross_loss = abs(d.loc[d.actual_r < 0, "actual_r"].sum())
        pf = gross_win / gross_loss if gross_loss else np.inf
        expectancy = d.actual_r.mean()
        avg_win = d.loc[d.actual_r > 0, "actual_r"].mean() if (d.actual_r > 0).any() else 0
        avg_loss = d.loc[d.actual_r < 0, "actual_r"].mean() if (d.actual_r < 0).any() else 0

        a,b,c,e,f = st.columns(5)
        a.metric("Trades", len(d))
        b.metric("Win rate", f"{wins/len(d)*100:.1f}%")
        c.metric("Net R", f"{d.actual_r.sum():+.2f}R")
        e.metric("Expectancy", f"{expectancy:+.2f}R")
        f.metric("Profit factor", "∞" if np.isinf(pf) else f"{pf:.2f}")

        section("Equity curve")
        d2 = d.sort_values(["trade_date","trade_time","id"]).copy()
        d2["equity_r"] = d2.actual_r.cumsum()
        premium_line_chart(d2, "id", ["equity_r"], ["Equity (R)"], height=300, zero_line=True)

        left, right = st.columns([1.35, 1])
        with left:
            section("Performance engine")
            engine = pd.DataFrame({
                "Metric": ["Average win", "Average loss", "Expectancy", "Gross profit", "Gross loss"],
                "Value": [f"{avg_win:+.2f}R", f"{avg_loss:+.2f}R", f"{expectancy:+.2f}R",
                          f"{gross_win:+.2f}R", f"-{gross_loss:.2f}R"]
            })
            st.dataframe(engine, use_container_width=True, hide_index=True)
        with right:
            section("Outcome distribution")
            premium_bar_chart(d.result.value_counts(), "Trade outcomes", height=250, value_suffix="")

        section("Recent execution")
        recent = d.head(8)
        for _, r in recent.iterrows():
            pill = result_pill(r["result"])
            rr = float(r["actual_r"])
            rr_class = "positive" if rr > 0 else "negative" if rr < 0 else "gold"
            st.markdown(
                f"""<div class="trade-row">
                <div>#{int(r['id'])}</div>
                <div><b>{r['market']}</b><br><span class="small-muted">{r['trade_date']} · {r['session']}</span></div>
                <div>{r['direction']}<br><span class="small-muted">{r['timeframe']}</span></div>
                <div class="{rr_class}"><b>{rr:+.2f}R</b></div>
                <div class="optional">{r.get('setup_name') or 'No setup'}</div>
                <div>{pill}</div>
                </div>""",
                unsafe_allow_html=True,
            )

        section("Process health")
        a,b,c = st.columns(3)
        a.metric("Rule adherence", f"{d.rule_adherence.mean():.1f}/10")
        b.metric("Setup quality", f"{d.setup_quality.mean():.1f}/10")
        c.metric("Confidence", f"{d.confidence.mean():.1f}/10")


# ------------------------------------------------------------
# TRADING CALENDAR
# ------------------------------------------------------------
elif current_key == "calendar":
    hero(
        "DAILY PERFORMANCE",
        "Trading Calendar",
        "See exactly how each trading day performed. Green days are net profit; red days are net loss.",
    )

    if not T:
        st.info("No trades recorded yet. Once you log trades, your daily profit and loss will appear here.")
    else:
        dcal = pd.DataFrame(T)
        dcal["date_obj"] = pd.to_datetime(dcal["trade_date"], errors="coerce").dt.date
        dcal["actual_r"] = pd.to_numeric(dcal["actual_r"], errors="coerce").fillna(0.0)
        dcal["pnl_money"] = pd.to_numeric(dcal["pnl_money"], errors="coerce").fillna(0.0)

        available_dates = dcal["date_obj"].dropna()
        min_year = int(min(available_dates).year) if len(available_dates) else date.today().year
        year_options = list(range(min_year, max(date.today().year, min_year) + 1))
        year_index = year_options.index(date.today().year) if date.today().year in year_options else len(year_options) - 1

        a, b = st.columns([1, 1])
        with a:
            cal_year = st.selectbox("Year", year_options, index=year_index)
        with b:
            cal_month = st.selectbox("Month", list(range(1, 13)), index=date.today().month - 1, format_func=lambda m: pycalendar.month_name[m])

        month_start = date(cal_year, cal_month, 1)
        month_end = date(cal_year, cal_month, pycalendar.monthrange(cal_year, cal_month)[1])
        dm = dcal[(dcal["date_obj"] >= month_start) & (dcal["date_obj"] <= month_end)].copy()

        daily = dm.groupby("date_obj", as_index=False).agg(
            pnl=("pnl_money", "sum"),
            net_r=("actual_r", "sum"),
            trades=("id", "count"),
            wins=("actual_r", lambda x: int((x > 0).sum())),
            losses=("actual_r", lambda x: int((x < 0).sum())),
        )
        daily_map = {r["date_obj"]: r for _, r in daily.iterrows()}

        net_pnl = float(dm["pnl_money"].sum()) if not dm.empty else 0.0
        net_r_month = float(dm["actual_r"].sum()) if not dm.empty else 0.0
        trading_days = len(daily)
        winning_days = int(sum(float(r["pnl"]) > 0 for r in daily_map.values()))
        losing_days = int(sum(float(r["pnl"]) < 0 for r in daily_map.values()))

        currency = PREF.get("currency", "USD")
        a, b, c, e = st.columns(4)
        a.metric("Monthly P/L", money(net_pnl, currency))
        b.metric("Net R", f"{net_r_month:+.2f}R")
        c.metric("Trading days", trading_days)
        e.metric("Win / Loss days", f"{winning_days} / {losing_days}")

        section(f"{pycalendar.month_name[cal_month]} {cal_year}")

        # Calendar grid: Monday → Sunday.
        weeks = pycalendar.monthcalendar(cal_year, cal_month)
        weekday_headers = "".join(f'<div class="cal-head">{x}</div>' for x in ["MON","TUE","WED","THU","FRI","SAT","SUN"])
        cells = []
        for week in weeks:
            for day_num in week:
                if day_num == 0:
                    cells.append('<div class="cal-cell cal-empty"></div>')
                    continue
                current_date = date(cal_year, cal_month, day_num)
                row = daily_map.get(current_date)
                if row is None:
                    cells.append(
                        f'<div class="cal-cell"><div class="cal-day">{day_num}</div><div class="cal-no-trade">No trade</div></div>'
                    )
                    continue

                pnl = float(row["pnl"])
                rr = float(row["net_r"])
                ntrades = int(row["trades"])
                cls = "cal-profit" if pnl > 0 else "cal-loss" if pnl < 0 else "cal-flat"
                sign = "+" if pnl > 0 else ""
                cells.append(
                    f'''<div class="cal-cell {cls}">
                        <div class="cal-day">{day_num}</div>
                        <div class="cal-pnl">{sign}{pnl:,.2f} {currency}</div>
                        <div class="cal-r">{rr:+.2f}R · {ntrades} trade{'s' if ntrades != 1 else ''}</div>
                    </div>'''
                )

        st.markdown(
            f'''<div class="calendar-wrap">
                <div class="calendar-grid calendar-header">{weekday_headers}</div>
                <div class="calendar-grid">{"".join(cells)}</div>
            </div>''',
            unsafe_allow_html=True,
        )

        section("Daily record")
        if daily.empty:
            st.caption("No trades were recorded in this month.")
        else:
            daily_display = daily.sort_values("date_obj", ascending=False).copy()
            daily_display["date_obj"] = daily_display["date_obj"].astype(str)
            daily_display["pnl"] = daily_display["pnl"].map(lambda x: money(x, currency))
            daily_display["net_r"] = daily_display["net_r"].map(lambda x: f"{x:+.2f}R")
            daily_display = daily_display.rename(columns={
                "date_obj": "Date", "pnl": "Daily P/L", "net_r": "Net R",
                "trades": "Trades", "wins": "Wins", "losses": "Losses"
            })
            st.dataframe(daily_display[["Date", "Daily P/L", "Net R", "Trades", "Wins", "Losses"]], use_container_width=True, hide_index=True)

# ------------------------------------------------------------
# ANALYSIS — admin-authored market analysis; everyone reads,
# likes and comments; only the admin publishes.
# ------------------------------------------------------------
elif current_key == "insights":
    hero(
        "MARKET INSIGHT",
        "Analysis",
        "Every write-up here is posted by Temexy directly. Read it, like it, discuss it in the comments below.",
    )

    if IS_ADMIN:
        with st.expander("＋ New analysis", expanded=False):
            with st.form("new_post_form", clear_on_submit=True):
                post_title = st.text_input("Title")
                post_content = st.text_area("Analysis", height=200)
                post_image = st.file_uploader("Optional chart / image", type=["png","jpg","jpeg"])
                if st.form_submit_button("Publish", use_container_width=True):
                    if not post_title.strip() or not post_content.strip():
                        st.warning("Title and analysis can't be empty.")
                    else:
                        add_post(
                            post_title.strip(),
                            post_content.strip(),
                            save_blog_image(post_image),
                            USER_NAME,
                            USER_ID,
                        )
                        st.success("Posted.")
                        st.rerun()

    posts = get_posts()
    if not posts:
        st.info(
            "Nothing posted yet. Use the form above to publish the first one."
            if IS_ADMIN else "Nothing posted yet — check back soon."
        )
    else:
        for post in posts:
            with st.container(border=True):
                st.markdown(
                    f"""<div class="post-title">{post['title']}</div>
                    <div class="post-meta">{post['author_name']} · {post['created_at'][:16].replace('T',' ')}</div>""",
                    unsafe_allow_html=True,
                )
                if post.get("image") and os.path.exists(post["image"]):
                    st.image(post["image"], use_container_width=True)
                st.markdown(f'<div class="post-body">{post["content"]}</div>', unsafe_allow_html=True)
                st.markdown("")

                liked = user_has_liked(post["id"], USER_ID)
                like_count = get_like_count(post["id"])
                comments = get_comments(post["id"])

                lcol, ccol, dcol = st.columns([1, 1, 2])
                with lcol:
                    like_label = f"♥ {like_count}" if liked else f"♡ {like_count}"
                    if st.button(like_label, key=f"like_{post['id']}", use_container_width=True):
                        toggle_like(post["id"], USER_ID)
                        st.rerun()
                with ccol:
                    st.caption(f"💬 {len(comments)} comment{'s' if len(comments) != 1 else ''}")
                with dcol:
                    if IS_ADMIN:
                        if st.button("Delete post", key=f"delpost_{post['id']}", use_container_width=True):
                            delete_post(post["id"])
                            st.rerun()

                with st.expander(f"Comments ({len(comments)})"):
                    for c in comments:
                        st.markdown(f"**{c['user_name']}**")
                        st.caption(c["created_at"][:16].replace("T", " "))
                        st.write(c["comment"])
                        if IS_ADMIN:
                            if st.button("Remove comment", key=f"delcomment_{c['id']}"):
                                delete_comment(c["id"])
                                st.rerun()
                        st.markdown("---")

                    new_comment = st.text_input("Add a comment", key=f"newcomment_{post['id']}")
                    if st.button("Post comment", key=f"submitcomment_{post['id']}", use_container_width=True):
                        if new_comment.strip():
                            add_comment(post["id"], USER_ID, USER_NAME, new_comment.strip())
                            st.rerun()


# ------------------------------------------------------------
# JOURNAL
# ------------------------------------------------------------
elif current_key == "journal":
    hero(
        "THE FULL RECORD",
        "Journal",
        "Search, filter and inspect every trade without losing the context around it.",
    )
    if not T:
        st.info("No trades recorded yet. Start with New Trade.")
    else:
        d = pd.DataFrame(T)
        d["actual_r"] = pd.to_numeric(d["actual_r"], errors="coerce").fillna(0)
        d["pnl_money"] = pd.to_numeric(d["pnl_money"], errors="coerce").fillna(0)

        a,b,c,dcol = st.columns(4)
        markets = sorted(d.market.dropna().unique().tolist())
        results = sorted(d.result.dropna().unique().tolist())
        directions = sorted(d.direction.dropna().unique().tolist())
        mf = a.multiselect("Market", markets)
        rf = b.multiselect("Result", results)
        dfilt = c.multiselect("Direction", directions)
        query = dcol.text_input("Search setup / tag / note")

        x = d.copy()
        if mf: x = x[x.market.isin(mf)]
        if rf: x = x[x.result.isin(rf)]
        if dfilt: x = x[x.direction.isin(dfilt)]
        if query:
            mask = (
                x.setup_name.fillna("").str.contains(query, case=False) |
                x.setup_tags.fillna("").str.contains(query, case=False) |
                x.reason.fillna("").str.contains(query, case=False) |
                x.lesson.fillna("").str.contains(query, case=False)
            )
            x = x[mask]

        st.caption(f"Showing {len(x)} of {len(d)} trades")

        display_cols = [
            "id","trade_date","trade_time","market","direction","timeframe",
            "session","setup_name","result","actual_r","pnl_money","rule_adherence"
        ]
        st.dataframe(
            x[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "actual_r": st.column_config.NumberColumn("R", format="%.2f"),
                "pnl_money": st.column_config.NumberColumn("P/L", format="%.2f"),
                "rule_adherence": st.column_config.NumberColumn("Rules", format="%.0f/10"),
            },
        )

        csv = x.to_csv(index=False).encode("utf-8")
        st.download_button(
            "↓ Export filtered journal (CSV)",
            data=csv,
            file_name=f"temexy_journal_{date.today().isoformat()}.csv",
            mime="text/csv",
        )


# ------------------------------------------------------------
# NEW TRADE
# ------------------------------------------------------------
elif current_key == "new-trade":
    hero(
        "LOG IT WHILE IT'S FRESH",
        "New trade",
        "Fast capture first. Advanced review second. The goal is a journal you will actually keep using.",
    )

    with st.form("trade_form"):
        section("01 · Trade identity")
        a,b,c = st.columns(3)
        with a:
            td = st.date_input("Date", date.today())
            market = st.selectbox("Market", ["XAUUSD","USDCHF","BTCUSD","EURUSD","US100","US30","Other"])
        with b:
            tt = st.time_input("Time", time(9,0))
            direction = st.selectbox("Direction", ["Buy","Sell"])
        with c:
            tf = st.selectbox("Timeframe", ["1M","5M","15M","30M","1H","4H","Daily"])
            session = st.selectbox("Session", ["Asia / Tokyo","London","New York","London/New York Overlap","Other"])

        section("02 · Setup")
        a,b = st.columns(2)
        with a:
            setup = st.text_input("Setup name", placeholder="Liquidity Sweep + MSS")
            tags = st.text_input("Setup tags", placeholder="FVG, CHOCH, OB, liquidity")
            bias = st.selectbox("HTF bias", ["Bullish","Bearish","Neutral","Not checked"])
        with b:
            reason = st.text_area("Why did I take it?", placeholder="What was the actual reason for entry?")
            context = st.text_area("Market context / structure", placeholder="What did price do before the entry?")

        section("03 · Risk & execution")
        a,b,c,dcol = st.columns(4)
        with a:
            entry = st.number_input("Entry", value=0.0, format="%.5f")
            sl = st.number_input("Stop Loss", value=0.0, format="%.5f")
        with b:
            tp = st.number_input("Take Profit", value=0.0, format="%.5f")
            exitp = st.number_input("Exit Price", value=0.0, format="%.5f")
        with c:
            prr = st.number_input("Planned RR", min_value=0.0, value=float(PREF.get("default_rr",2)), step=.1)
            riskpct = st.number_input("Risk %", min_value=0.0, value=float(PREF.get("max_risk",1)), step=.1)
        with dcol:
            riskmoney = st.number_input("Risk money", min_value=0.0, value=0.0, step=1.0)
            ar = st.number_input("Actual result (R)", value=0.0, step=.1)

        a,b,c = st.columns(3)
        with a:
            pnl = st.number_input("P/L money", value=0.0, step=1.0)
            result = st.selectbox("Result", ["Win","Loss","Break-even","Partial / Mixed"])
        with b:
            conf = st.slider("Confidence", 1, 10, 5)
            quality = st.slider("Setup quality", 1, 10, 5)
        with c:
            adherence = st.slider("Rule adherence", 1, 10, 5)
            news = st.text_input("News / event", placeholder="CPI, NFP, FOMC, none")

        with st.expander("Advanced review · psychology & execution"):
            a,b,c = st.columns(3)
            with a:
                execution = st.text_area("Execution notes")
                eb = st.text_area("Before trade")
            with b:
                ed = st.text_area("During trade")
                ea = st.text_area("After trade")
            with c:
                went = st.text_area("What went well?")
                mistake = st.text_area("Mistake")
            lesson = st.text_area("Lesson")
            change = st.text_area("What will I change next time?")

        with st.expander("Chart evidence"):
            a,b,c = st.columns(3)
            with a: before = st.file_uploader("Before entry", type=["png","jpg","jpeg"])
            with b: setupimg = st.file_uploader("Setup / entry", type=["png","jpg","jpeg"])
            with c: after = st.file_uploader("After exit", type=["png","jpg","jpeg"])

        submit = st.form_submit_button("SAVE TRADE", use_container_width=True)

    if submit:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data = {
            "user_id":USER_ID, "trade_date":td.isoformat(), "trade_time":tt.strftime("%H:%M"),
            "market":market, "direction":direction, "timeframe":tf, "session":session,
            "setup_name":setup, "setup_tags":tags, "htf_bias":bias, "entry":entry,
            "stop_loss":sl, "take_profit":tp, "exit_price":exitp, "planned_rr":prr,
            "actual_r":ar, "pnl_money":pnl, "risk_percent":riskpct, "risk_money":riskmoney,
            "result":result, "confidence":conf, "rule_adherence":adherence,
            "setup_quality":quality, "news_event":news, "market_context":context,
            "reason":reason, "execution":execution, "emotion_before":eb,
            "emotion_during":ed, "emotion_after":ea, "mistake":mistake,
            "lesson":lesson, "what_went_well":went, "what_to_change":change,
            "screenshot_before":saveimg(before, stamp+"_before", USER_ID),
            "screenshot_setup":saveimg(setupimg, stamp+"_setup", USER_ID),
            "screenshot_after":saveimg(after, stamp+"_after", USER_ID),
            "created_at":datetime.now().isoformat(),
        }
        i = add_trade(data)
        st.success(f"Trade #{i} saved.")
        st.session_state.page = "journal"
        st.rerun()


# ------------------------------------------------------------
# TRADE DETAIL
# ------------------------------------------------------------
elif current_key == "detail":
    hero(
        "ONE TRADE, IN FULL",
        "Trade detail",
        "Numbers, chart evidence, context and psychology in one review screen.",
    )
    if not T:
        st.info("No trades yet.")
    else:
        opts = {
            f"#{t['id']} · {t['trade_date']} · {t['market']} · {t['direction']} · {t['result']}": t["id"]
            for t in T
        }
        label = st.selectbox("Select trade", list(opts))
        t = get_trade(opts[label], USER_ID)

        a,b,c,d,e = st.columns(5)
        a.metric("Result", t["result"])
        b.metric("R", num(t["actual_r"]))
        c.metric("P/L", money(t["pnl_money"], PREF.get("currency","USD")))
        d.metric("Planned RR", num(t["planned_rr"]))
        e.metric("Rules", f"{t['rule_adherence']}/10")

        a,b = st.columns(2)
        with a:
            section("Trade information")
            st.write(f"**Date:** {t['trade_date']} {t['trade_time']}")
            st.write(f"**Market:** {t['market']}")
            st.write(f"**Direction:** {t['direction']}")
            st.write(f"**Timeframe:** {t['timeframe']}")
            st.write(f"**Session:** {t['session']}")
            st.write(f"**Setup:** {t['setup_name'] or '—'}")
            st.write(f"**Tags:** {t['setup_tags'] or '—'}")
            st.write(f"**HTF bias:** {t['htf_bias']}")
            st.write(f"**News:** {t['news_event'] or '—'}")
        with b:
            section("Risk & numbers")
            st.write(f"**Entry:** {num(t['entry'])}")
            st.write(f"**SL:** {num(t['stop_loss'])}")
            st.write(f"**TP:** {num(t['take_profit'])}")
            st.write(f"**Exit:** {num(t['exit_price'])}")
            st.write(f"**Risk:** {num(t['risk_percent'])}% / {money(t['risk_money'], PREF.get('currency','USD'))}")
            st.write(f"**Confidence:** {t['confidence']}/10")
            st.write(f"**Setup quality:** {t['setup_quality']}/10")

        section("Chart record")
        cols = st.columns(3)
        for col, title, key in zip(
            cols,
            ["Before entry","Setup / entry","After exit"],
            ["screenshot_before","screenshot_setup","screenshot_after"],
        ):
            with col:
                st.markdown(f"**{title}**")
                p = t.get(key)
                if p and os.path.exists(p):
                    st.image(p, use_container_width=True)
                else:
                    st.caption("No image.")

        notes = [
            ("Why I took it","reason"),("Market context","market_context"),
            ("Execution","execution"),("Before","emotion_before"),
            ("During","emotion_during"),("After","emotion_after"),
            ("What went well","what_went_well"),("Mistake","mistake"),
            ("Lesson","lesson"),("What I will change","what_to_change"),
        ]
        for title, key in notes:
            if t.get(key):
                section(title)
                st.write(t[key])

        if st.button("Delete this trade"):
            remove_trade(t["id"], USER_ID)
            st.success("Trade deleted.")
            st.rerun()


# ------------------------------------------------------------
# ANALYTICS
# ------------------------------------------------------------
elif current_key == "analytics":
    hero(
        "PERFORMANCE INTELLIGENCE",
        "Analytics",
        "Turn the journal into evidence: expectancy, drawdown, streaks, sessions, markets, setups and discipline.",
    )
    if not T:
        st.info("Record trades first.")
    else:
        d = pd.DataFrame(T)
        d["actual_r"] = pd.to_numeric(d["actual_r"], errors="coerce").fillna(0)
        d["pnl_money"] = pd.to_numeric(d["pnl_money"], errors="coerce").fillna(0)
        for col in ["rule_adherence","setup_quality","confidence"]:
            d[col] = pd.to_numeric(d[col], errors="coerce")

        d = d.sort_values(["trade_date","trade_time","id"]).reset_index(drop=True)
        d["equity_r"] = d.actual_r.cumsum()
        d["peak_r"] = d.equity_r.cummax()
        d["drawdown_r"] = d.equity_r - d.peak_r
        max_dd = abs(d.drawdown_r.min())
        wins_mask = d.actual_r > 0
        losses_mask = d.actual_r < 0
        gross_win = d.loc[wins_mask,"actual_r"].sum()
        gross_loss = abs(d.loc[losses_mask,"actual_r"].sum())
        pf = gross_win/gross_loss if gross_loss else np.inf
        expectancy = d.actual_r.mean()
        avg_win = d.loc[wins_mask,"actual_r"].mean() if wins_mask.any() else 0
        avg_loss = d.loc[losses_mask,"actual_r"].mean() if losses_mask.any() else 0

        a,b,c,e,f = st.columns(5)
        a.metric("Expectancy", f"{expectancy:+.2f}R")
        b.metric("Max drawdown", f"-{max_dd:.2f}R")
        c.metric("Avg win", f"{avg_win:+.2f}R")
        e.metric("Avg loss", f"{avg_loss:+.2f}R")
        f.metric("Profit factor", "∞" if np.isinf(pf) else f"{pf:.2f}")

        section("Equity & drawdown")
        premium_line_chart(d, "id", ["equity_r","drawdown_r"], ["Equity (R)","Drawdown (R)"], height=315, zero_line=True)

        section("Where performance comes from")
        for title, col in [
            ("By market","market"),("By setup","setup_name"),
            ("By session","session"),("By direction","direction"),
            ("By timeframe","timeframe")
        ]:
            g = d.groupby(col, dropna=False).agg(
                Trades=("id","count"),
                Net_R=("actual_r","sum"),
                Avg_R=("actual_r","mean"),
                Wins=("result", lambda x: int((x=="Win").sum())),
                Losses=("result", lambda x: int((x=="Loss").sum())),
            ).reset_index()
            g["Win_Rate_%"] = g["Wins"] / g["Trades"] * 100
            with st.expander(title, expanded=(title=="By market")):
                st.dataframe(g, use_container_width=True, hide_index=True)

        section("Discipline vs outcome")
        discipline = d.groupby("result")[["rule_adherence","setup_quality","confidence"]].mean().round(2)
        st.dataframe(discipline, use_container_width=True)

        section("Calendar")
        d["date_obj"] = pd.to_datetime(d.trade_date)
        monthly = d.groupby(d.date_obj.dt.to_period("M").astype(str)).actual_r.sum()
        premium_bar_chart(monthly, "Monthly net R", height=240, value_suffix="R")

        section("Streaks")
        outcomes = ["W" if x > 0 else "L" if x < 0 else "B" for x in d.actual_r]
        best_win = best_loss = cur_win = cur_loss = 0
        for x in outcomes:
            if x == "W":
                cur_win += 1; cur_loss = 0
            elif x == "L":
                cur_loss += 1; cur_win = 0
            else:
                cur_win = cur_loss = 0
            best_win = max(best_win, cur_win)
            best_loss = max(best_loss, cur_loss)
        a,b,c = st.columns(3)
        a.metric("Best win streak", best_win)
        b.metric("Worst loss streak", best_loss)
        c.metric("Trades logged", len(d))


# ------------------------------------------------------------
# RISK LAB / COMPOUNDING
# ------------------------------------------------------------
elif current_key == "risk":
    hero(
        "CAPITAL MANAGEMENT",
        "Risk Lab",
        "Model your account before you trade. Plan the path, stress-test drawdown and see how compounding behaves.",
    )

    section("Compounding calculator")
    a,b,c = st.columns(3)
    with a:
        start = st.number_input("Starting balance", min_value=0.0, value=float(PREF.get("starting_balance") or 100.0), step=10.0)
        risk = st.number_input("Risk per trade (%)", min_value=0.0, value=float(PREF.get("max_risk") or 1.0), step=.1)
    with b:
        rr = st.number_input("Reward : Risk", min_value=0.0, value=float(PREF.get("default_rr") or 2.0), step=.1)
        wins_pct = st.number_input("Expected win rate (%)", min_value=0.0, max_value=100.0, value=50.0, step=1.0)
    with c:
        trades_n = st.number_input("Number of trades", min_value=1, max_value=1000, value=50, step=1)
        mode = st.selectbox("Risk model", ["Compound every trade","Fixed initial risk"])

    if st.button("Calculate projection", type="primary"):
        balance = float(start)
        rows = []
        fixed_risk = start * risk / 100
        expected_r = (wins_pct/100 * rr) - ((100-wins_pct)/100 * 1)
        for i in range(1, int(trades_n)+1):
            risk_money = balance * risk/100 if mode == "Compound every trade" else fixed_risk
            # Expected-value path: expected R per trade.
            pnl = risk_money * expected_r
            balance += pnl
            rows.append({"Trade":i, "Risk $":risk_money, "Expected R":expected_r, "Projected Balance":balance})
        proj = pd.DataFrame(rows)
        st.metric("Expected R / trade", f"{expected_r:+.2f}R")
        st.metric("Projected ending balance", money(balance, PREF.get("currency","USD")))
        premium_line_chart(proj, "Trade", ["Projected Balance"], ["Projected balance"], height=285)
        st.dataframe(proj.tail(10), use_container_width=True, hide_index=True)
        st.caption("This is a mathematical expectation path, not a forecast of actual trading results.")

    section("Drawdown simulator")
    a,b,c = st.columns(3)
    with a:
        dd_risk = st.number_input("Risk per loss (%)", min_value=0.0, value=1.0, step=.1, key="ddrisk")
    with b:
        losses = st.number_input("Consecutive losses", min_value=0, value=5, step=1)
    with c:
        account_after = start * ((1-dd_risk/100) ** losses)
        st.metric("Balance after streak", money(account_after, PREF.get("currency","USD")))
    if start > 0:
        st.progress(min(max(account_after/start, 0), 1))
        st.caption(f"Approximate drawdown from {losses} consecutive losses: {(1-account_after/start)*100:.2f}%")

    section("Compounding reference")
    ref = []
    bal = float(start)
    for i in range(1, min(int(trades_n), 100)+1):
        risk_money = bal * risk/100
        bal += risk_money * rr
        ref.append({"Trade":i,"Balance after a +RR winner":bal})
    st.dataframe(pd.DataFrame(ref).tail(10), use_container_width=True, hide_index=True)


# ------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------
elif current_key == "settings":
    hero(
        "WORKSPACE CONTROL",
        "Settings",
        "Personalize your account defaults, export your records and understand exactly what this journal stores.",
    )

    section("Trading defaults")
    with st.form("settings_form"):
        a,b,c = st.columns(3)
        with a:
            starting_balance = st.number_input("Starting balance", min_value=0.0, value=float(PREF.get("starting_balance") or 0), step=10.0)
            currency = st.selectbox("Currency", ["USD","NGN","GBP","EUR"], index=["USD","NGN","GBP","EUR"].index(PREF.get("currency","USD")))
        with b:
            monthly_goal = st.number_input("Monthly goal", min_value=0.0, value=float(PREF.get("monthly_goal") or 0), step=10.0)
            max_risk = st.number_input("Default risk %", min_value=0.0, value=float(PREF.get("max_risk") or 1), step=.1)
        with c:
            default_rr = st.number_input("Default RR", min_value=0.0, value=float(PREF.get("default_rr") or 2), step=.1)
            st.caption("These defaults pre-fill new trades and Risk Lab. They do not place orders.")
        if st.form_submit_button("Save workspace settings", use_container_width=True):
            save_preferences(USER_ID, starting_balance, currency, monthly_goal, max_risk, default_rr)
            st.success("Settings saved.")
            st.rerun()

    section("Account")
    st.markdown(
        f"""<div class="card">
        <div class="card-title">Signed in as</div>
        <div class="card-value" style="font-size:18px">{USER_NAME}</div>
        <div class="card-sub">{USER_EMAIL}</div>
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button("Log out", key="settings_logout", use_container_width=True):
        st.logout()

    section("Data & backup")
    if T:
        export = pd.DataFrame(T).to_csv(index=False).encode("utf-8")
        st.download_button(
            "↓ Download complete journal CSV",
            data=export,
            file_name=f"temexy_trade_journal_{date.today().isoformat()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    st.warning(
        "Streamlit Cloud's local filesystem is not a permanent database. "
        "For a serious long-term journal, connect persistent storage/database and keep periodic exports."
    )

    section("What TEMEXY tracks")
    included = [
        "Trade date, time, market, direction, timeframe and session",
        "Setup name, tags and higher-timeframe bias",
        "Entry, stop, target, exit, planned RR, actual R and money P/L",
        "Risk percentage and risk amount",
        "Win / loss / break-even / partial result",
        "Confidence, setup quality and rule adherence",
        "News, market context, reason for entry and execution",
        "Before / during / after emotions",
        "Mistakes, lessons, what went well and what changes next time",
        "Before-entry, setup-entry and after-exit screenshots",
        "Performance by market, setup, session, direction and timeframe",
        "Expectancy, profit factor, equity curve, drawdown and streak analysis",
        "Compounding, risk and drawdown modelling",
    ]
    for item in included:
        st.write("✓ " + item)

    if IS_ADMIN:
        section("Admin")
        users_list = all_users()
        a,b = st.columns(2)
        a.metric("People signed in", len(users_list))
        b.metric("Trades across all accounts", total_trade_count())
        if users_list:
            udf = pd.DataFrame(users_list)
            st.dataframe(
                udf[["name","email","first_seen","last_seen"]],
                use_container_width=True,
                hide_index=True,
            )

    st.markdown("---")
    st.caption("TEMEXY TRADE JOURNAL • Evidence over emotion • Process over outcome")
