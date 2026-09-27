import os
import sqlite3
import uuid
import math
from pathlib import Path
from datetime import datetime, date, time

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image


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
  --bg:#090908;
  --panel:#121210;
  --panel2:#171714;
  --panel3:#1E1D19;
  --text:#F7F2E9;
  --muted:#9D978D;
  --muted2:#726D65;
  --line:rgba(247,242,233,.09);
  --line2:rgba(247,242,233,.14);
  --orange:#FF7A45;
  --orange2:#F4A261;
  --gold:#E6BB67;
  --green:#63D39B;
  --red:#E86A63;
  --blue:#7FB7FF;
}

*{box-sizing:border-box}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{
  background:
    radial-gradient(circle at 8% -8%,rgba(255,122,69,.12),transparent 26%),
    radial-gradient(circle at 94% 3%,rgba(230,187,103,.07),transparent 24%),
    linear-gradient(145deg,#090908 0%,#0E0E0C 50%,#080807 100%);
  color:var(--text);
}
[data-testid="stSidebar"]{display:none}
[data-testid="stHeader"]{background:transparent}
.block-container{max-width:1520px;padding:1rem 2rem 4rem}
h1,h2,h3{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.035em}
h1{font-size:2.25rem!important}
h2{font-size:1.55rem!important}
h3{font-size:1.08rem!important}
p,label,.stCaption{color:#B8B1A7}

/* top shell */
.top-shell{
  position:sticky;top:8px;z-index:999;
  margin-bottom:18px;
  background:rgba(15,15,13,.90);
  border:1px solid var(--line);
  border-radius:22px;
  box-shadow:0 22px 70px rgba(0,0,0,.35);
  backdrop-filter:blur(22px);
}
.top-main{display:flex;align-items:center;gap:18px;padding:13px 15px}
.brand{display:flex;align-items:center;gap:10px;min-width:180px}
.brand-mark{
  width:43px;height:43px;border-radius:13px;display:grid;place-items:center;
  background:linear-gradient(145deg,#FF7A45,#D95D36);
  box-shadow:0 8px 26px rgba(255,122,69,.18)
}
.brand-mark svg{width:26px;height:26px}
.brand-name{font-family:'Space Grotesk';font-size:18px;font-weight:700;letter-spacing:.12em}
.brand-tag{font-size:8px;letter-spacing:.22em;color:#847E76;font-weight:700}
.user-chip{
  margin-left:auto;border-left:1px solid var(--line);padding-left:16px;
  color:#9D978D;font-size:11px;white-space:nowrap
}
.user-chip b{color:#F7F2E9}

/* nav */
.nav-scroll{display:flex;gap:7px;padding:0 15px 13px;overflow-x:auto;scrollbar-width:none}
.nav-scroll::-webkit-scrollbar{display:none}
div[data-testid="stHorizontalBlock"] .stButton>button{
  min-height:38px;font-size:12px;padding:0 12px;border-radius:10px;
  transition:all .16s ease;box-shadow:none!important;white-space:nowrap
}
button[kind="secondary"]{
  background:#151513!important;color:#C9C2B7!important;
  border:1px solid var(--line)!important;font-weight:700!important
}
button[kind="secondary"]:hover{
  background:#211F1C!important;color:#F7F2E9!important;
  border-color:var(--line2)!important
}
button[kind="primary"]{
  background:linear-gradient(135deg,#FF7A45,#E9683D)!important;
  color:#171311!important;border-color:#FF7A45!important;font-weight:800!important
}

/* hero */
.hero{
  position:relative;overflow:hidden;
  padding:27px 30px;margin:4px 0 22px;
  border:1px solid var(--line);border-radius:25px;
  background:
    radial-gradient(circle at 88% 12%,rgba(255,122,69,.13),transparent 23%),
    linear-gradient(135deg,#181815,#10100E);
  box-shadow:0 20px 65px rgba(0,0,0,.25)
}
.hero:after{
  content:'';position:absolute;width:300px;height:300px;right:-125px;top:-150px;
  border:1px solid rgba(255,122,69,.15);border-radius:50%
}
.hero-kicker{color:#FF9A70;font-size:10px;font-weight:800;letter-spacing:.19em;text-transform:uppercase}
.hero-title{font-family:'Space Grotesk';font-size:32px;font-weight:700;margin:5px 0;color:#F7F2E9}
.hero-sub{color:#AAA39A;font-size:14px;max-width:900px;line-height:1.55}

/* cards */
[data-testid="metric-container"]{
  background:linear-gradient(145deg,#181816,#10100F);
  border:1px solid var(--line);padding:15px 17px;border-radius:17px;
  box-shadow:0 12px 35px rgba(0,0,0,.18)
}
[data-testid="stMetricLabel"]{color:#999289!important;font-size:11px!important}
[data-testid="stMetricValue"]{color:#F7F2E9!important;font-family:'Space Grotesk'}
.card{
  background:linear-gradient(145deg,#171714,#10100F);
  border:1px solid var(--line);border-radius:18px;padding:18px;
  box-shadow:0 14px 40px rgba(0,0,0,.16);height:100%
}
.card-title{font-family:'Space Grotesk';font-weight:700;color:#F1EBE1;font-size:14px;margin-bottom:7px}
.card-value{font-family:'Space Grotesk';font-size:27px;font-weight:700;color:#F7F2E9}
.card-sub{font-size:11px;color:#89837B;margin-top:4px}
.section-title{
  display:flex;align-items:center;gap:9px;margin:24px 0 11px;
  font-family:'Space Grotesk';font-size:16px;font-weight:700;color:#EEE7DD
}
.section-dot{width:7px;height:7px;border-radius:50%;background:var(--orange);box-shadow:0 0 14px rgba(255,122,69,.55)}
.small-muted{color:#827C73;font-size:11px}
.positive{color:var(--green)!important}.negative{color:var(--red)!important}.gold{color:var(--gold)!important}

/* controls */
.stButton>button,.stFormSubmitButton>button{
  border-radius:11px!important;min-height:43px;
  border:1px solid rgba(255,255,255,.09)!important;
  background:linear-gradient(135deg,#FF7A45,#E9683D)!important;
  color:#171311!important;font-weight:800!important;
  box-shadow:0 8px 22px rgba(255,122,69,.12)
}
.stButton>button:hover,.stFormSubmitButton>button:hover{transform:translateY(-1px);border-color:rgba(255,255,255,.2)!important}
.stTextInput input,.stNumberInput input,.stTextArea textarea,
.stSelectbox div[data-baseweb="select"]>div,.stDateInput input,.stTimeInput input{
  background:#151513!important;color:#F4EFE7!important;
  border:1px solid var(--line)!important;border-radius:10px!important
}
[data-testid="stExpander"],[data-testid="stForm"]{
  border:1px solid var(--line);border-radius:18px;background:rgba(18,18,16,.72)
}
[data-testid="stForm"]{padding:9px 8px}
[data-testid="stFileUploaderDropzone"]{
  background:#151513!important;border:1px dashed rgba(255,122,69,.28)!important;border-radius:14px!important
}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:15px;overflow:hidden}
.stProgress > div > div{background:var(--orange)!important}
hr{border-color:var(--line)!important}
footer{visibility:hidden}
a{color:#FF9A70!important}

/* table-like trade rows */
.trade-row{
  display:grid;grid-template-columns:74px 1.3fr .8fr .7fr .7fr .7fr;
  gap:12px;align-items:center;padding:13px 14px;
  border-bottom:1px solid var(--line);font-size:12px
}
.trade-row:first-child{border-top:1px solid var(--line)}
.trade-row:hover{background:rgba(255,255,255,.025)}
.pill{
  display:inline-flex;align-items:center;justify-content:center;
  border:1px solid var(--line);border-radius:999px;padding:4px 8px;
  font-size:10px;font-weight:700;background:#171714
}
.pill-win{color:var(--green);border-color:rgba(99,211,155,.22);background:rgba(99,211,155,.06)}
.pill-loss{color:var(--red);border-color:rgba(232,106,99,.22);background:rgba(232,106,99,.06)}
.pill-be{color:var(--gold);border-color:rgba(230,187,103,.22);background:rgba(230,187,103,.05)}
.thumb{
  width:100%;height:92px;object-fit:cover;border-radius:12px;
  border:1px solid var(--line);background:#0D0D0B
}

/* responsive */
@media(max-width:900px){
  .block-container{padding:.7rem .8rem 3rem}
  .top-main{gap:10px;padding:10px}
  .brand{min-width:auto}
  .user-chip{display:none}
  .hero{padding:22px 19px;border-radius:20px}
  .hero-title{font-size:25px}
  h1{font-size:1.85rem!important}
  h2{font-size:1.35rem!important}
  .trade-row{grid-template-columns:62px 1fr .65fr .7fr;font-size:11px}
  .trade-row .optional{display:none}
}
@media(max-width:560px){
  .block-container{padding:.55rem .55rem 2.5rem}
  .brand-name{font-size:16px}.brand-mark{width:38px;height:38px}
  .nav-scroll{padding:0 8px 9px}
  .hero{margin-bottom:15px;padding:19px 16px}
  .hero-title{font-size:23px}
  .hero-sub{font-size:12px}
  [data-testid="metric-container"]{padding:12px 12px;border-radius:14px}
  .card{padding:14px;border-radius:15px}
  .stButton>button,.stFormSubmitButton>button{min-height:40px;font-size:12px}
  .trade-row{grid-template-columns:56px 1fr .7fr}
  .trade-row .hide-mobile{display:none}
}

/* Streamlit's native charts sit nicely inside our dark UI */
[data-testid="stVegaLiteChart"],[data-testid="stArrowVegaLiteChart"]{
  background:#11110F;border:1px solid var(--line);border-radius:15px;padding:6px
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
    "journal": "Journal",
    "new-trade": "New Trade",
    "detail": "Trade Detail",
    "analytics": "Analytics",
    "risk": "Risk Lab",
    "settings": "Settings",
}
NAV_ITEMS = list(PAGE_MAP.items())

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
            st.session_state.page = key
            st.rerun()


# ------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------
if current_key == "dashboard":
    hero(
        "TEMEXY • PERFORMANCE CENTER",
        "Trade with evidence. Review without emotion.",
        "A professional trading workspace built around execution, risk, psychology and measurable performance.",
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
        st.line_chart(d2.set_index("id")[["equity_r"]], height=280)

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
            st.bar_chart(d.result.value_counts())

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
        st.line_chart(d.set_index("id")[["equity_r","drawdown_r"]], height=300)

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
        st.bar_chart(monthly, height=220)

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
        "Model your account before you trade. The calculator is educational: actual broker/prop rules can differ.",
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
        st.line_chart(proj.set_index("Trade")[["Projected Balance"]], height=280)
        st.dataframe(proj.tail(10), use_container_width=True, hide_index=True)
        st.caption("This is a mathematical expectation path, not a forecast of actual trading results.")

    section("Risk / position calculator")
    a,b,c,dcol = st.columns(4)
    with a:
        balance2 = st.number_input("Account balance", min_value=0.0, value=float(start), step=10.0, key="bal2")
        risk2 = st.number_input("Risk (%)", min_value=0.0, value=float(risk), step=.1, key="risk2")
    with b:
        stop_distance = st.number_input("Stop distance (points/pips)", min_value=0.0, value=0.0, step=.1)
        value_per_unit = st.number_input("Value per 1 unit / point", min_value=0.0, value=1.0, step=.1)
    with c:
        risk_amount = balance2 * risk2 / 100
        st.metric("Money at risk", money(risk_amount, PREF.get("currency","USD")))
    with dcol:
        position_size = risk_amount/(stop_distance*value_per_unit) if stop_distance and value_per_unit else 0
        st.metric("Illustrative size", f"{position_size:.4f}")

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
