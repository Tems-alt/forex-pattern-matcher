import os, sqlite3, uuid
from pathlib import Path
from datetime import datetime, date, time
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter

st.set_page_config(page_title='Temexy Trade Journal', page_icon='📈', layout='wide', initial_sidebar_state='collapsed')

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root{
  --bg:#0B0B0A;
  --panel:#151514;
  --panel2:#1B1B19;
  --panel3:#22221F;
  --text:#F5F0E8;
  --muted:#A8A197;
  --line:rgba(245,240,232,.10);
  --orange:#FF7A45;
  --orange2:#F4A261;
  --gold:#E5B85C;
  --green:#63D39B;
  --red:#E86A63;
}

html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{
  background:
    radial-gradient(circle at 12% -10%,rgba(255,122,69,.13),transparent 27%),
    radial-gradient(circle at 90% 8%,rgba(229,184,92,.08),transparent 25%),
    linear-gradient(145deg,#0B0B0A 0%,#10100F 52%,#0A0A09 100%);
  color:var(--text);
}
[data-testid="stSidebar"]{display:none}
[data-testid="stHeader"]{background:transparent}
.block-container{max-width:1500px;padding:1.2rem 2.2rem 4rem}

h1,h2,h3{
  font-family:'Space Grotesk',sans-serif!important;
  letter-spacing:-.025em
}
h1{font-size:2.35rem!important}
h2{font-size:1.6rem!important}
h3{font-size:1.12rem!important}
p,label,.stCaption{color:#B8B1A7}

.topbar{
  display:flex;
  align-items:center;
  gap:22px;
  padding:14px 16px;
  margin-bottom:18px;
  background:rgba(20,20,18,.92);
  border:1px solid rgba(245,240,232,.10);
  border-radius:20px;
  box-shadow:0 18px 55px rgba(0,0,0,.28);
  position:sticky;
  top:8px;
  z-index:99;
  backdrop-filter:blur(18px);
}
.brand{
  display:flex;
  align-items:center;
  gap:11px;
  min-width:190px;
}
.brand-mark{
  width:44px;height:44px;border-radius:14px;
  display:grid;place-items:center;
  background:linear-gradient(145deg,#FF7A45,#D95D36);
  box-shadow:0 8px 26px rgba(255,122,69,.20);
}
.brand-mark svg{width:27px;height:27px}
.brand-name{
  font-family:'Space Grotesk';
  font-size:19px;font-weight:700;
  letter-spacing:.12em;color:#F7F1E8
}
.brand-tag{
  font-size:8px;letter-spacing:.22em;
  color:#938C82;font-weight:700;margin-top:1px
}
.topbar-meta{
  margin-left:auto;
  display:flex;align-items:center;gap:8px;
  color:#A8A197;font-size:12px;font-weight:600;
  white-space:nowrap
}
.topbar-meta b{color:#F4EFE6}

/* Premium top navigation */
.nav-wrap{display:flex;align-items:center;gap:10px;flex:1;min-width:0}
.nav-link{display:inline-flex;align-items:center;justify-content:center;height:40px;padding:0 14px;border-radius:10px;color:#BDB5AA!important;text-decoration:none!important;font-size:12px;font-weight:700;letter-spacing:.01em;border:1px solid transparent;transition:all .18s ease;white-space:nowrap}
.nav-link:hover{color:#F6F0E8!important;background:#211F1C;border-color:rgba(245,240,232,.10)}
.nav-link.active{color:#17130F!important;background:#F29B57;border-color:#F29B57;box-shadow:0 7px 22px rgba(242,155,87,.16)}
.topbar-meta{margin-left:auto;display:flex;align-items:center;gap:14px;color:#8F877D;font-size:11px;font-weight:700;letter-spacing:.08em;white-space:nowrap;border-left:1px solid rgba(245,240,232,.08);padding-left:18px}
.topbar-meta b{color:#F4EFE6;letter-spacing:0}
@media(max-width:1050px){.topbar{flex-wrap:wrap}.nav-wrap{order:3;width:100%;overflow-x:auto;padding-top:3px}.topbar-meta{margin-left:0;border-left:0;padding-left:0}}
.temexy-hero{
  padding:30px 34px;
  border:1px solid rgba(245,240,232,.10);
  border-radius:26px;
  background:
    radial-gradient(circle at 88% 20%,rgba(255,122,69,.14),transparent 24%),
    linear-gradient(135deg,#191817,#111110);
  box-shadow:0 20px 70px rgba(0,0,0,.28);
  margin-bottom:24px;
  position:relative;overflow:hidden
}
.temexy-hero:after{
  content:'';position:absolute;width:260px;height:260px;
  right:-90px;top:-110px;border-radius:50%;
  border:1px solid rgba(255,122,69,.18)
}
.hero-kicker{color:#FF9A70;font-size:11px;font-weight:800;letter-spacing:.18em;text-transform:uppercase}
.hero-title{color:#F7F1E8;font-family:'Space Grotesk';font-size:34px;font-weight:700;margin:6px 0}
.hero-sub{color:#AAA39A;font-size:15px;max-width:800px}

[data-testid="metric-container"]{
  background:linear-gradient(145deg,#191918,#121211);
  border:1px solid var(--line);
  padding:17px 18px;
  border-radius:18px;
  box-shadow:0 12px 35px rgba(0,0,0,.18)
}
[data-testid="stMetricLabel"]{color:#9F988E!important}
[data-testid="stMetricValue"]{color:#F5F0E8!important;font-family:'Space Grotesk'}

.stButton>button,.stFormSubmitButton>button{
  border-radius:12px!important;
  border:1px solid rgba(255,255,255,.09)!important;
  background:linear-gradient(135deg,#FF7A45,#E9683D)!important;
  color:#171311!important;
  font-weight:800!important;
  min-height:44px;
  box-shadow:0 9px 24px rgba(255,122,69,.14)
}
.stButton>button:hover,.stFormSubmitButton>button:hover{
  border-color:rgba(255,255,255,.24)!important;
  transform:translateY(-1px)
}

.stTextInput input,.stNumberInput input,.stTextArea textarea,
.stSelectbox div[data-baseweb="select"]>div,.stDateInput input,.stTimeInput input{
  background:#171716!important;
  color:#F4EFE7!important;
  border:1px solid rgba(245,240,232,.10)!important;
  border-radius:11px!important
}
[data-testid="stExpander"]{
  border:1px solid var(--line);
  border-radius:16px;
  background:rgba(22,22,20,.72)
}
[data-testid="stForm"]{
  border:1px solid var(--line);
  border-radius:22px;
  padding:10px 8px;
  background:rgba(18,18,17,.72)
}
[data-testid="stDataFrame"]{
  border:1px solid var(--line);
  border-radius:16px;
  overflow:hidden
}
.section-title{
  display:flex;align-items:center;gap:10px;
  margin:22px 0 12px;
  font-family:'Space Grotesk';
  font-size:17px;font-weight:700;color:#EFE8DE
}
.section-dot{
  width:8px;height:8px;border-radius:50%;
  background:var(--orange);
  box-shadow:0 0 14px rgba(255,122,69,.55)
}
.small-muted{color:#8F887F;font-size:12px}

[data-testid="stFileUploaderDropzone"]{
  background:#171716!important;
  border:1px dashed rgba(255,122,69,.30)!important;
  border-radius:16px!important
}
.stProgress > div > div{background:var(--orange)!important}
a{color:#FF9A70!important}
hr{border-color:rgba(245,240,232,.08)!important}
footer{visibility:hidden}

/* Native nav row (replaces the old <a href> links — no more new-tab navigation) */
div[data-testid="stHorizontalBlock"] .stButton>button{
  min-height:38px;font-size:12.5px;padding:0 6px;border-radius:10px;
  transition:all .15s ease;box-shadow:none!important
}
button[kind="secondary"]{
  background:#171614!important;color:#C9C2B7!important;
  border:1px solid rgba(245,240,232,.10)!important;font-weight:700!important
}
button[kind="secondary"]:hover{
  background:#211f1c!important;color:#F6F0E8!important;
  border-color:rgba(245,240,232,.20)!important
}
button[kind="primary"]{
  background:linear-gradient(135deg,#FF7A45,#E9683D)!important;
  color:#171311!important;border-color:#FF7A45!important
}
/* Chat bubbles for the AI Assistant */
[data-testid="stChatMessage"]{
  background:rgba(22,22,20,.72)!important;border:1px solid var(--line)!important;
  border-radius:16px!important
}

@media(max-width:1050px){
  .topbar{align-items:flex-start;flex-direction:column}
  .topbar-meta{margin-left:0}
  .brand{min-width:auto}
}
</style>
""", unsafe_allow_html=True)

BASE=Path('trade_journal_data'); IMG=BASE/'images'; DB=BASE/'trades.db'; IMG.mkdir(parents=True,exist_ok=True)

def conn():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init():
    c=conn(); c.execute('''CREATE TABLE IF NOT EXISTS trades(
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, trade_date TEXT, trade_time TEXT, market TEXT,
    direction TEXT, timeframe TEXT, session TEXT, setup_name TEXT, setup_tags TEXT,
    htf_bias TEXT, entry REAL, stop_loss REAL, take_profit REAL, exit_price REAL,
    planned_rr REAL, actual_r REAL, pnl_money REAL, risk_percent REAL, risk_money REAL,
    result TEXT, confidence INTEGER, rule_adherence INTEGER, setup_quality INTEGER,
    news_event TEXT, market_context TEXT, reason TEXT, execution TEXT,
    emotion_before TEXT, emotion_during TEXT, emotion_after TEXT, mistake TEXT,
    lesson TEXT, what_went_well TEXT, what_to_change TEXT, screenshot_before TEXT,
    screenshot_setup TEXT, screenshot_after TEXT, created_at TEXT)''')
    # Migration for DBs created before multi-user support existed.
    try: c.execute('ALTER TABLE trades ADD COLUMN user_id TEXT')
    except sqlite3.OperationalError: pass
    c.commit(); c.close()
init()

def trades(user_id):
    c=conn(); x=[dict(r) for r in c.execute('SELECT * FROM trades WHERE user_id=? ORDER BY trade_date DESC,trade_time DESC,id DESC',(user_id,))]; c.close(); return x

def get(tid,user_id):
    c=conn(); r=c.execute('SELECT * FROM trades WHERE id=? AND user_id=?',(tid,user_id)).fetchone(); c.close(); return dict(r) if r else None

def add(d):
    c=conn(); cols=list(d); c.execute(f"INSERT INTO trades({','.join(cols)}) VALUES({','.join(['?']*len(cols))})",[d[x] for x in cols]); c.commit(); i=c.execute('SELECT last_insert_rowid()').fetchone()[0]; c.close(); return i

def remove(tid,user_id):
    t=get(tid,user_id)
    if not t: return
    for k in ('screenshot_before','screenshot_setup','screenshot_after'):
        p=t.get(k)
        if p:
            try: Path(p).unlink(missing_ok=True)
            except: pass
    c=conn(); c.execute('DELETE FROM trades WHERE id=? AND user_id=?',(tid,user_id)); c.commit(); c.close()

def saveimg(f,prefix,user_id):
    if not f:return None
    udir=IMG/user_id; udir.mkdir(parents=True,exist_ok=True)
    p=udir/f'{prefix}_{uuid.uuid4().hex[:8]}.png'; Image.open(f).convert('RGB').save(p,'PNG'); return str(p)

def feature(source):
    im=Image.open(source).convert('RGB') if isinstance(source,(str,Path)) else Image.open(source).convert('RGB')
    w,h=im.size; im=im.crop((int(w*.04),int(h*.06),int(w*.98),int(h*.96))).convert('L')
    im=ImageEnhance.Contrast(im).enhance(2).filter(ImageFilter.SHARPEN)
    tw=th=96; s=max(tw/im.width,th/im.height); im=im.resize((int(im.width*s),int(im.height*s)),Image.Resampling.LANCZOS)
    x=(im.width-tw)//2; y=(im.height-th)//2; a=np.asarray(im.crop((x,y,x+tw,y+th)),dtype=np.float32)/255
    gx=np.diff(a,axis=1); gy=np.diff(a,axis=0); gx=np.pad(gx,((0,0),(0,1))); gy=np.pad(gy,((0,1),(0,0))); e=np.sqrt(gx*gx+gy*gy)
    def sm(z,n=32): return np.asarray(Image.fromarray(np.uint8(np.clip(z,0,1)*255)).resize((n,n)),dtype=np.float32).ravel()/255
    f=np.r_[sm(a),sm(e/(e.max()+1e-6)),a.mean(0),a.mean(1),e.mean(0),e.mean(1)].astype(np.float32); n=np.linalg.norm(f); return f/n if n else f

def money(x):
    try:return f'{float(x):,.2f}'
    except:return '—'

def num(x):
    try:return f'{float(x):.2f}'
    except:return '—'

def hero(kicker, title, sub):
    st.markdown(
        f'<div class="temexy-hero"><div class="hero-kicker">{kicker}</div>'
        f'<div class="hero-title">{title}</div><div class="hero-sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )

def section(title):
    st.markdown(f'<div class="section-title"><span class="section-dot"></span>{title}</div>', unsafe_allow_html=True)

# ------------------------------------------------------------
# GOOGLE SIGN-IN — gates the whole app. Nothing below this runs
# for a signed-out visitor, and every query below is scoped to
# the signed-in user's own id (st.user.sub), so one person can
# never see another person's trades.
# ------------------------------------------------------------
if not st.user.is_logged_in:
    st.markdown(
        '<div class="temexy-hero" style="max-width:520px;margin:8vh auto 0;text-align:center">'
        '<div class="hero-kicker">TEMEXY • TRADE JOURNAL</div>'
        '<div class="hero-title" style="font-size:26px">Sign in to see your journal</div>'
        '<div class="hero-sub">Every account gets its own private trades, screenshots and AI assistant. '
        'Nobody else can see your data, and you can\'t see theirs.</div></div>',
        unsafe_allow_html=True,
    )
    _, mid, _ = st.columns([1,1,1])
    with mid:
        if st.button('Continue with Google', use_container_width=True, type='primary'):
            st.login('google')
    st.stop()

USER_ID = st.user.sub
USER_NAME = st.user.get('name') or st.user.get('email') or 'Trader'
T=trades(USER_ID)

top_l, top_r = st.columns([6,1])
with top_l:
    st.caption(f'Signed in as **{USER_NAME}**')
with top_r:
    if st.button('Log out', use_container_width=True):
        st.logout()

# ------------------------------------------------------------
# ------------------------------------------------------------
# TOP NAVIGATION — clean product-style header
# ------------------------------------------------------------
page_map={
    'dashboard':'🏠 Dashboard',
    'new-trade':'➕ New Trade',
    'history':'📖 Trade History',
    'detail':'🔎 Trade Detail',
    'analytics':'📊 Analytics',
    'setups':'📚 Setup Library',
    'assistant':'🤖 AI Assistant',
    'settings':'⚙️ Settings',
}
NAV_ITEMS=[('dashboard','🏠 Dashboard'),('new-trade','➕ New Trade'),('history','📖 Trade History'),
           ('detail','🔎 Trade Detail'),('analytics','📊 Analytics'),('setups','📚 Setup Library'),
           ('assistant','🤖 AI Assistant'),('settings','⚙️ Settings')]

if 'page' not in st.session_state:
    st.session_state.page='dashboard'
current_key=st.session_state.page
if current_key not in page_map: current_key='dashboard'
page=page_map[current_key]

wins=sum(x['result']=='Win' for x in T) if T else 0
net=sum(float(x['actual_r'] or 0) for x in T) if T else 0
win_rate=(wins/len(T)*100) if T else 0

# Brand + live stats strip (pure display, no links — nothing here can hijack a tab)
brand_html=(
  '<div class="topbar"><div class="brand"><div class="brand-mark"><svg viewBox="0 0 40 40" fill="none" '
  'xmlns="http://www.w3.org/2000/svg"><path d="M7 29V16L13 22L19 13L25 19L33 7" stroke="#171311" stroke-width="3" '
  'stroke-linecap="round" stroke-linejoin="round"/><path d="M12 9V29M8.5 13H15.5M8.5 19H15.5" stroke="#F8E5C2" '
  'stroke-width="2.2" stroke-linecap="round"/></svg></div><div><div class="brand-name">TEMEXY</div>'
  '<div class="brand-tag">TRADE JOURNAL</div></div></div>'
  f'<div class="topbar-meta"><span>TRADES <b>{len(T)}</b></span><span>WIN RATE <b>{win_rate:.1f}%</b></span>'
  f'<span>NET <b>{net:+.2f}R</b></span></div></div>'
)
st.markdown(brand_html, unsafe_allow_html=True)

# Real Streamlit buttons drive navigation now — a click only changes session_state
# and reruns the script, so it can never open a new browser tab the way the old
# <a href="?page=..."> links sometimes did.
nav_cols=st.columns(len(NAV_ITEMS))
for col,(key,label) in zip(nav_cols,NAV_ITEMS):
    with col:
        if st.button(label, key=f'nav_{key}', use_container_width=True,
                     type=('primary' if key==current_key else 'secondary')):
            st.session_state.page=key
            st.rerun()
st.write('')

if current_key=='dashboard':
    hero('TEMEXY • PERFORMANCE CENTER', 'Trade with evidence. Review without emotion.',
         'Your setups, execution, risk, psychology and results — organized into one clean trading command center.')
    section('Performance Snapshot')
    if not T: st.info('No trades yet. Go to ➕ New Trade.')
    else:
        d=pd.DataFrame(T); d['actual_r']=pd.to_numeric(d.actual_r,errors='coerce').fillna(0); d['pnl_money']=pd.to_numeric(d.pnl_money,errors='coerce').fillna(0)
        wins=(d.result=='Win').sum(); total=len(d); pf=d.loc[d.actual_r>0,'actual_r'].sum()/abs(d.loc[d.actual_r<0,'actual_r'].sum()) if (d.actual_r<0).any() else np.inf
        a,b,c,e,f=st.columns(5); a.metric('Trades',total); b.metric('Win Rate',f'{wins/total*100:.1f}%'); c.metric('Net R',f'{d.actual_r.sum():+.2f}R'); e.metric('Avg R',f'{d.actual_r.mean():+.2f}R'); f.metric('Profit Factor','∞' if np.isinf(pf) else f'{pf:.2f}')
        l,r=st.columns(2)
        with l:
            st.subheader('📈 Equity Curve'); q=d.sort_values(['trade_date','trade_time','id'])['actual_r'].cumsum(); st.line_chart(pd.DataFrame({'Cumulative R':q.values},index=range(1,len(q)+1)))
        with r:
            st.subheader('🎯 Results'); st.bar_chart(d.result.value_counts())
        a,b,c=st.columns(3); a.metric('Avg Rule Adherence',f'{pd.to_numeric(d.rule_adherence,errors="coerce").mean():.1f}/10'); b.metric('Avg Setup Quality',f'{pd.to_numeric(d.setup_quality,errors="coerce").mean():.1f}/10'); c.metric('Avg Confidence',f'{pd.to_numeric(d.confidence,errors="coerce").mean():.1f}/10')
        st.subheader('Recent Trades'); st.dataframe(d.head(10)[['id','trade_date','market','direction','timeframe','setup_name','result','actual_r','pnl_money']],use_container_width=True,hide_index=True)

elif current_key=='new-trade':
    hero('LOG IT WHILE IT\'S FRESH', 'Record a new trade', 'Keep it factual, keep it quick — a clean record now saves you from guessing later.')
    with st.form('trade'):
        st.subheader('1. Identification'); a,b,c=st.columns(3)
        with a: td=st.date_input('Date',date.today()); market=st.selectbox('Market',['XAUUSD','USDCHF','BTCUSD','EURUSD','US100','Other'])
        with b: tt=st.time_input('Time',time(9,0)); direction=st.selectbox('Direction',['Buy','Sell'])
        with c: tf=st.selectbox('Timeframe',['1M','5M','15M','30M','1H','4H','Daily']); session=st.selectbox('Session',['Asia / Tokyo','London','New York','London/New York Overlap','Other'])
        st.subheader('2. Setup & Context'); a,b=st.columns(2)
        with a: setup=st.text_input('Setup Name',placeholder='Liquidity Sweep + MSS'); tags=st.text_input('Setup Tags',placeholder='FVG, CHOCH, sweep, OB'); bias=st.selectbox('HTF Bias',['Bullish','Bearish','Neutral','Not checked']); reason=st.text_area('Why did I take it?')
        with b: context=st.text_area('Market Context / Structure'); news=st.text_input('News / Event',placeholder='CPI, NFP, FOMC, none'); execution=st.text_area('Execution notes',placeholder='Entry quality, spread, slippage, management...')
        st.subheader('3. Numbers'); a,b,c,d=st.columns(4)
        with a: entry=st.number_input('Entry',value=0.0,format='%.5f'); sl=st.number_input('Stop Loss',value=0.0,format='%.5f')
        with b: tp=st.number_input('Take Profit',value=0.0,format='%.5f'); exitp=st.number_input('Exit Price',value=0.0,format='%.5f')
        with c: prr=st.number_input('Planned RR',min_value=0.0,value=2.0,step=.1); riskpct=st.number_input('Risk %',min_value=0.0,value=1.0,step=.1)
        with d: riskmoney=st.number_input('Risk Money',min_value=0.0,value=0.0,step=1.0); ar=st.number_input('Actual Result (R)',value=0.0,step=.1)
        a,b,c=st.columns(3)
        with a: pnl=st.number_input('P/L Money',value=0.0,step=1.0); result=st.selectbox('Result',['Win','Loss','Break-even','Partial / Mixed'])
        with b: conf=st.slider('Confidence',1,10,5); quality=st.slider('Setup Quality',1,10,5)
        with c: adherence=st.slider('Rule Adherence',1,10,5)
        st.subheader('4. Psychology'); a,b,c=st.columns(3)
        with a: eb=st.text_area('Before Trade'); ed=st.text_area('During Trade')
        with b: ea=st.text_area('After Trade'); went=st.text_area('What went well?')
        with c: mistake=st.text_area('Mistake'); lesson=st.text_area('Lesson')
        change=st.text_area('What will I change next time?')
        st.subheader('5. Screenshots'); a,b,c=st.columns(3)
        with a: before=st.file_uploader('Before Entry',type=['png','jpg','jpeg'])
        with b: setupimg=st.file_uploader('Setup / Entry',type=['png','jpg','jpeg'])
        with c: after=st.file_uploader('After Exit',type=['png','jpg','jpeg'])
        submit=st.form_submit_button('💾 SAVE TRADE',use_container_width=True)
    if submit:
        stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
        data={'user_id':USER_ID,'trade_date':td.isoformat(),'trade_time':tt.strftime('%H:%M'),'market':market,'direction':direction,'timeframe':tf,'session':session,'setup_name':setup,'setup_tags':tags,'htf_bias':bias,'entry':entry,'stop_loss':sl,'take_profit':tp,'exit_price':exitp,'planned_rr':prr,'actual_r':ar,'pnl_money':pnl,'risk_percent':riskpct,'risk_money':riskmoney,'result':result,'confidence':conf,'rule_adherence':adherence,'setup_quality':quality,'news_event':news,'market_context':context,'reason':reason,'execution':execution,'emotion_before':eb,'emotion_during':ed,'emotion_after':ea,'mistake':mistake,'lesson':lesson,'what_went_well':went,'what_to_change':change,'screenshot_before':saveimg(before,stamp+'_before',USER_ID),'screenshot_setup':saveimg(setupimg,stamp+'_setup',USER_ID),'screenshot_after':saveimg(after,stamp+'_after',USER_ID),'created_at':datetime.now().isoformat()}
        i=add(data); st.success(f'Trade #{i} saved.'); st.balloons()

elif current_key=='history':
    hero('THE FULL RECORD', 'Trade history', 'Every trade you\'ve logged, filterable by market, result, direction and setup.')
    if not T: st.info('No trades recorded yet.')
    else:
        d=pd.DataFrame(T); a,b,c,e=st.columns(4)
        mf=a.multiselect('Market',sorted(d.market.unique()),default=[]); rf=b.multiselect('Result',sorted(d.result.unique()),default=[]); dfilt=c.multiselect('Direction',sorted(d.direction.unique()),default=[]); q=e.text_input('Search setup / tags')
        x=d.copy()
        if mf:x=x[x.market.isin(mf)]
        if rf:x=x[x.result.isin(rf)]
        if dfilt:x=x[x.direction.isin(dfilt)]
        if q:x=x[x.setup_name.fillna('').str.contains(q,case=False)|x.setup_tags.fillna('').str.contains(q,case=False)]
        st.write(f'Showing **{len(x)}** of **{len(d)}** trades.'); st.dataframe(x[['id','trade_date','trade_time','market','direction','timeframe','session','setup_name','result','actual_r','pnl_money','rule_adherence']],use_container_width=True,hide_index=True)

elif current_key=='detail':
    hero('ONE TRADE, IN FULL', 'Trade detail', 'Everything you recorded about a single trade — numbers, context, psychology and chart evidence.')
    if not T: st.info('No trades yet.')
    else:
        opts={f"#{t['id']} · {t['trade_date']} · {t['market']} · {t['direction']} · {t['result']}":t['id'] for t in T}; label=st.selectbox('Select trade',list(opts)); t=get(opts[label],USER_ID)
        a,b,c,d,e=st.columns(5); a.metric('Result',t['result']); b.metric('R',num(t['actual_r'])); c.metric('P/L',money(t['pnl_money'])); d.metric('Planned RR',num(t['planned_rr'])); e.metric('Rules',f"{t['rule_adherence']}/10")
        l,r=st.columns(2)
        with l:
            section('📌 Trade Information'); st.write(f"**Date:** {t['trade_date']} {t['trade_time']}"); st.write(f"**Market:** {t['market']}"); st.write(f"**Direction:** {t['direction']}"); st.write(f"**Timeframe:** {t['timeframe']}"); st.write(f"**Session:** {t['session']}"); st.write(f"**Setup:** {t['setup_name']}"); st.write(f"**Tags:** {t['setup_tags']}"); st.write(f"**HTF Bias:** {t['htf_bias']}"); st.write(f"**News:** {t['news_event']}")
        with r:
            section('💰 Numbers'); st.write(f"**Entry:** {num(t['entry'])}"); st.write(f"**SL:** {num(t['stop_loss'])}"); st.write(f"**TP:** {num(t['take_profit'])}"); st.write(f"**Exit:** {num(t['exit_price'])}"); st.write(f"**Risk:** {num(t['risk_percent'])}% / {money(t['risk_money'])}"); st.write(f"**Confidence:** {t['confidence']}/10"); st.write(f"**Setup Quality:** {t['setup_quality']}/10")
        section('🖼️ Chart Record'); cols=st.columns(3)
        for col,title,k in zip(cols,['Before Entry','Setup / Entry','After Exit'],['screenshot_before','screenshot_setup','screenshot_after']):
            with col:
                st.markdown(f'**{title}**'); p=t[k]
                if p and os.path.exists(p):st.image(p,use_container_width=True)
                else:st.caption('No image.')
        for title,k in [('🧠 Why I Took It','reason'),('🌍 Market Context','market_context'),('⚙️ Execution','execution'),('😐 Before','emotion_before'),('😰 During','emotion_during'),('😌 After','emotion_after'),('✅ What Went Well','what_went_well'),('❌ Mistake','mistake'),('💡 Lesson','lesson'),('🔁 What I Will Change','what_to_change')]:
            if t[k]: section(title); st.write(t[k])
        if st.button('🗑️ Delete This Trade'): remove(t['id'],USER_ID); st.success('Deleted.'); st.rerun()

elif current_key=='analytics':
    hero('WHERE YOUR EDGE ACTUALLY LIVES', 'Trading analytics', 'Let the journal show you where your performance really comes from — by market, setup, session and direction.')
    if not T: st.info('Record trades first.')
    else:
        d=pd.DataFrame(T); d['actual_r']=pd.to_numeric(d.actual_r,errors='coerce').fillna(0); d['rule_adherence']=pd.to_numeric(d.rule_adherence,errors='coerce'); d['setup_quality']=pd.to_numeric(d.setup_quality,errors='coerce'); d['confidence']=pd.to_numeric(d.confidence,errors='coerce')
        for title,col in [('By Market','market'),('By Setup','setup_name'),('By Session','session'),('By Direction','direction')]:
            section(title); g=d.groupby(col).agg(Trades=('id','count'),Net_R=('actual_r','sum'),Avg_R=('actual_r','mean'),Wins=('result',lambda x:(x=='Win').sum()),Losses=('result',lambda x:(x=='Loss').sum())).reset_index(); g['Win_Rate_%']=g.Wins/g.Trades*100; st.dataframe(g,use_container_width=True,hide_index=True)
        section('Discipline vs Result'); st.dataframe(d.groupby('result')[['rule_adherence','setup_quality','confidence']].mean(),use_container_width=True)
        section('Monthly R'); d['month']=pd.to_datetime(d.trade_date).dt.to_period('M').astype(str); st.bar_chart(d.groupby('month').actual_r.sum())

elif current_key=='setups':
    hero('VISUAL PATTERN MEMORY', 'Setup library', 'Upload a new chart and retrieve the closest historical formations. Your old Buy/Sell labels do not control the visual match.')
    q=st.file_uploader('New chart to compare',type=['png','jpg','jpeg'])
    if q and T:
        qv=feature(q); res=[]
        for t in T:
            p=t.get('screenshot_setup') or t.get('screenshot_before')
            if p and os.path.exists(p):
                try: res.append((float(np.dot(qv,feature(p))),t,p))
                except: pass
        res.sort(reverse=True,key=lambda z:z[0]); st.success(f'Found {len(res)} saved chart records.'); top=res[:9]
        for i in range(0,len(top),3):
            row=top[i:i+3]; cols=st.columns(len(row))
            for col,(score,t,p) in zip(cols,row):
                with col:
                    st.image(p,use_container_width=True); st.markdown(f"**#{t['id']} — {score*100:.1f}% visual similarity**"); st.write(f"{t['market']} · {t['timeframe']} · {t['direction']} · {t['result']}"); st.caption(t['setup_name'] or 'Unnamed setup')
    elif not T: st.info('Record trades with screenshots first.')
    st.markdown('---'); section('Saved Setup Screenshots')
    for t in T:
        p=t.get('screenshot_setup') or t.get('screenshot_before')
        if p and os.path.exists(p):
            with st.expander(f"#{t['id']} · {t['market']} · {t['setup_name']} · {t['result']}"): st.image(p,width=700); st.write(f"{t['direction']} · {t['timeframe']} · {t['session']} · {t['actual_r']}R")

elif current_key=='assistant':
    hero('YOUR JOURNAL, ASKED A QUESTION', 'AI assistant', 'Ask it about your own trades — it reads a summary of your logged performance before answering.')

    with st.expander('🔑 API key & model', expanded=not st.session_state.get('anthropic_key')):
        st.caption(
            'This runs from *your own* Anthropic API key — Temexy has no server, so there\'s nowhere else '
            'for it to come from. Get a key at console.anthropic.com. It stays in this browser session only; '
            'it is never written to the journal database or disk.'
        )
        key_input=st.text_input('Anthropic API key', type='password',
                                 value=st.session_state.get('anthropic_key',''), key='key_input_field')
        model_choice=st.selectbox('Model', ['claude-sonnet-5','claude-opus-5-5','claude-haiku-4-5-20251001'],
                                   index=['claude-sonnet-5','claude-opus-5-5','claude-haiku-4-5-20251001'].index(
                                       st.session_state.get('anthropic_model','claude-sonnet-5')))
        if st.button('Save key for this session'):
            st.session_state.anthropic_key=key_input
            st.session_state.anthropic_model=model_choice
            st.success('Saved for this session.')

    def _journal_summary():
        if not T: return 'The journal is empty — no trades logged yet.'
        d=pd.DataFrame(T)
        d['actual_r']=pd.to_numeric(d.actual_r,errors='coerce').fillna(0)
        wins=int((d.result=='Win').sum()); losses=int((d.result=='Loss').sum()); total=len(d)
        by_setup=d.groupby('setup_name')['actual_r'].agg(['count','sum','mean']).round(2).to_dict('index')
        by_market=d.groupby('market')['actual_r'].agg(['count','sum','mean']).round(2).to_dict('index')
        recent_notes=[f"- {r['trade_date']} {r['market']} {r['result']} ({r['actual_r']}R): "
                      f"mistake={r.get('mistake') or 'none noted'}; lesson={r.get('lesson') or 'none noted'}"
                      for r in d.tail(8).to_dict('records')]
        return (
            f"Total trades: {total}. Wins: {wins}. Losses: {losses}. Net R: {d.actual_r.sum():+.2f}. "
            f"Avg R: {d.actual_r.mean():+.2f}.\n"
            f"By setup: {by_setup}\nBy market: {by_market}\n"
            f"Last 8 trades (notes):\n" + "\n".join(recent_notes)
        )

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history=[]

    def _call_claude(user_text):
        api_key=st.session_state.get('anthropic_key','') or os.environ.get('ANTHROPIC_API_KEY','')
        if not api_key:
            return "I need an API key first — add one above under '🔑 API key & model'."
        try:
            import requests
        except ImportError:
            return "This feature needs the `requests` package — install it with `pip install requests`."
        system_prompt=(
            "You are a trading-performance assistant embedded in the user's personal trade journal app. "
            "Answer using ONLY the journal summary given below plus the conversation — do not invent trades "
            "or numbers that aren't there. Be direct and specific; point to actual setups/markets/mistakes "
            "from the data when relevant. Keep answers concise.\n\nJOURNAL SUMMARY:\n" + _journal_summary()
        )
        messages=[{"role":m["role"],"content":m["content"]} for m in st.session_state.chat_history]
        messages.append({"role":"user","content":user_text})
        try:
            resp=requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key":api_key,
                    "anthropic-version":"2023-06-01",
                    "content-type":"application/json",
                },
                json={
                    "model":st.session_state.get('anthropic_model','claude-sonnet-5'),
                    "max_tokens":700,
                    "system":system_prompt,
                    "messages":messages,
                },
                timeout=30,
            )
            resp.raise_for_status()
            blocks=resp.json().get("content",[])
            return "".join(b.get("text","") for b in blocks if b.get("type")=="text") or "(empty response)"
        except Exception as e:
            return f"Request failed: {e}"

    quick1,quick2=st.columns(2)
    if quick1.button('📋 Summarize my performance', use_container_width=True):
        st.session_state.chat_history.append({"role":"user","content":"Summarize my overall performance and the single biggest thing I should fix."})
        st.session_state.chat_history.append({"role":"assistant","content":_call_claude(st.session_state.chat_history[-1]["content"])})
    if quick2.button('🧠 What mistake do I repeat most?', use_container_width=True):
        st.session_state.chat_history.append({"role":"user","content":"Looking at my logged mistakes across trades, what pattern repeats the most and how should I address it?"})
        st.session_state.chat_history.append({"role":"assistant","content":_call_claude(st.session_state.chat_history[-1]["content"])})

    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    user_msg=st.chat_input('Ask about your trades...')
    if user_msg:
        st.session_state.chat_history.append({"role":"user","content":user_msg})
        with st.chat_message("user"):
            st.write(user_msg)
        with st.chat_message("assistant"):
            with st.spinner('Reading your journal...'):
                reply=_call_claude(user_msg)
            st.write(reply)
        st.session_state.chat_history.append({"role":"assistant","content":reply})

    if st.session_state.chat_history and st.button('Clear conversation'):
        st.session_state.chat_history=[]
        st.rerun()

elif current_key=='settings':
    hero('WHAT THIS JOURNAL TRACKS', 'Settings', 'Where your data lives, and everything this journal is built to record.')
    st.info('This journal records the complete trade lifecycle: setup, market context, numbers, execution, psychology, mistakes, lessons, and chart evidence.')
    section('Included');
    for x in ['Trade date/time','Market, direction, timeframe and session','Setup name and tags','HTF bias','Entry, SL, TP and exit','Planned RR, actual R, risk % and money','Win/Loss/BE','Confidence, setup quality and rule adherence','News and market context','Reason for entry and execution notes','Before/during/after emotions','Mistakes, lessons and next change','Before/setup/after screenshots','Visual setup similarity search','Market/setup/session/direction analytics','Equity curve and monthly performance']:
        st.write('✅ '+x)
    st.warning('Important for Streamlit Cloud: this version stores the SQLite database and screenshots in the app filesystem. For a permanent cloud journal, connect persistent storage/database before building a large archive.')
    st.code(str(BASE))

st.markdown('---'); st.caption('TEMEXY TRADE JOURNAL • Evidence over emotion • Process over outcome')
