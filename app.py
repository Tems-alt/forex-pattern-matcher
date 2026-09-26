import os, sqlite3, uuid
from pathlib import Path
from datetime import datetime, date, time
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter

st.set_page_config(page_title='Temexy Trade Journal', page_icon='📈', layout='wide', initial_sidebar_state='expanded')

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--bg:#06111F;--panel:#10253F;--text:#F5F8FC;--muted:#9EB0C7;--line:rgba(255,255,255,.09);--teal:#22D3A7;--blue:#5B8CFF;--gold:#F6C85F;--purple:#B78CFF}
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.stApp{background:radial-gradient(circle at 8% 0%,rgba(91,140,255,.18),transparent 28%),radial-gradient(circle at 92% 4%,rgba(34,211,167,.13),transparent 26%),linear-gradient(135deg,#06111F 0%,#091A2F 48%,#071426 100%);color:var(--text)}
[data-testid="stHeader"]{background:transparent}[data-testid="stSidebar"]{background:linear-gradient(180deg,#071426 0%,#0A1930 100%);border-right:1px solid var(--line)}
[data-testid="stSidebar"] .stRadio label{color:#B7C5D8;font-weight:600}.block-container{max-width:1450px;padding-top:2rem;padding-bottom:4rem}
h1,h2,h3{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.025em}h1{font-size:2.5rem!important}h2{font-size:1.65rem!important}h3{font-size:1.18rem!important}p,label,.stCaption{color:#B4C1D3}
.temexy-hero{padding:28px 32px;border:1px solid rgba(255,255,255,.10);border-radius:24px;background:linear-gradient(135deg,rgba(18,43,72,.94),rgba(11,27,48,.86));box-shadow:0 18px 60px rgba(0,0,0,.25);margin-bottom:24px;position:relative;overflow:hidden}.temexy-hero:after{content:'';position:absolute;width:260px;height:260px;right:-80px;top:-100px;border-radius:50%;background:rgba(34,211,167,.10);filter:blur(10px)}
.hero-kicker{color:#7FE7D0;font-size:12px;font-weight:800;letter-spacing:.18em;text-transform:uppercase}.hero-title{color:#F8FBFF;font-family:'Space Grotesk';font-size:34px;font-weight:700;margin:6px 0}.hero-sub{color:#AAB9CD;font-size:15px;max-width:780px}
[data-testid="metric-container"]{background:linear-gradient(145deg,rgba(18,43,72,.94),rgba(11,29,49,.94));border:1px solid var(--line);padding:17px 18px;border-radius:18px;box-shadow:0 10px 30px rgba(0,0,0,.14)}[data-testid="stMetricLabel"]{color:#9EB0C7!important}[data-testid="stMetricValue"]{color:#F7FAFF!important;font-family:'Space Grotesk'}
.stButton>button,.stFormSubmitButton>button{border-radius:12px;border:1px solid rgba(255,255,255,.10);background:linear-gradient(135deg,#1B7C73,#2467A8);color:white;font-weight:800;min-height:44px;box-shadow:0 8px 20px rgba(22,105,128,.18)}.stButton>button:hover,.stFormSubmitButton>button:hover{border-color:rgba(255,255,255,.3);transform:translateY(-1px)}
.stTextInput input,.stNumberInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"]>div,.stDateInput input,.stTimeInput input{background:#0D2139!important;color:#F4F7FB!important;border:1px solid rgba(255,255,255,.10)!important;border-radius:11px!important}
[data-testid="stExpander"]{border:1px solid var(--line);border-radius:16px;background:rgba(13,33,57,.62)}[data-testid="stForm"]{border:1px solid var(--line);border-radius:22px;padding:8px 6px;background:rgba(10,27,47,.58)}[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:16px;overflow:hidden}
.section-title{display:flex;align-items:center;gap:10px;margin:22px 0 12px;font-family:'Space Grotesk';font-size:17px;font-weight:700;color:#EEF4FB}.section-dot{width:8px;height:8px;border-radius:50%;background:linear-gradient(135deg,var(--teal),var(--blue));box-shadow:0 0 14px rgba(34,211,167,.55)}.small-muted{color:#8FA2BA;font-size:12px}
.logo-wrap{padding:4px 4px 18px}.logo-box{display:flex;align-items:center;gap:11px}.logo-mark{width:42px;height:42px;border-radius:13px;background:linear-gradient(135deg,#1DD5AA,#477FFF 65%,#A878FF);display:grid;place-items:center;box-shadow:0 8px 24px rgba(55,137,210,.28)}.logo-mark svg{width:26px;height:26px}.logo-name{font-family:'Space Grotesk';font-size:18px;font-weight:800;letter-spacing:.12em;color:#F4F8FD}.logo-tag{font-size:9px;letter-spacing:.2em;color:#7F94AF;font-weight:700;margin-top:2px}footer{visibility:hidden}
</style>
""", unsafe_allow_html=True)
BASE=Path('trade_journal_data'); IMG=BASE/'images'; DB=BASE/'trades.db'; IMG.mkdir(parents=True,exist_ok=True)

def conn():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init():
    c=conn(); c.execute('''CREATE TABLE IF NOT EXISTS trades(
    id INTEGER PRIMARY KEY AUTOINCREMENT, trade_date TEXT, trade_time TEXT, market TEXT,
    direction TEXT, timeframe TEXT, session TEXT, setup_name TEXT, setup_tags TEXT,
    htf_bias TEXT, entry REAL, stop_loss REAL, take_profit REAL, exit_price REAL,
    planned_rr REAL, actual_r REAL, pnl_money REAL, risk_percent REAL, risk_money REAL,
    result TEXT, confidence INTEGER, rule_adherence INTEGER, setup_quality INTEGER,
    news_event TEXT, market_context TEXT, reason TEXT, execution TEXT,
    emotion_before TEXT, emotion_during TEXT, emotion_after TEXT, mistake TEXT,
    lesson TEXT, what_went_well TEXT, what_to_change TEXT, screenshot_before TEXT,
    screenshot_setup TEXT, screenshot_after TEXT, created_at TEXT)'''); c.commit(); c.close()
init()

def trades():
    c=conn(); x=[dict(r) for r in c.execute('SELECT * FROM trades ORDER BY trade_date DESC,trade_time DESC,id DESC')]; c.close(); return x

def get(tid):
    c=conn(); r=c.execute('SELECT * FROM trades WHERE id=?',(tid,)).fetchone(); c.close(); return dict(r) if r else None

def add(d):
    c=conn(); cols=list(d); c.execute(f"INSERT INTO trades({','.join(cols)}) VALUES({','.join(['?']*len(cols))})",[d[x] for x in cols]); c.commit(); i=c.execute('SELECT last_insert_rowid()').fetchone()[0]; c.close(); return i

def remove(tid):
    t=get(tid)
    if t:
        for k in ('screenshot_before','screenshot_setup','screenshot_after'):
            p=t.get(k)
            if p:
                try: Path(p).unlink(missing_ok=True)
                except: pass
    c=conn(); c.execute('DELETE FROM trades WHERE id=?',(tid,)); c.commit(); c.close()

def saveimg(f,prefix):
    if not f:return None
    p=IMG/f'{prefix}_{uuid.uuid4().hex[:8]}.png'; Image.open(f).convert('RGB').save(p,'PNG'); return str(p)

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

T=trades()
st.sidebar.markdown('<div class="logo-wrap"><div class="logo-box"><div class="logo-mark"><svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M7 29L7 16M7 16L13 22L19 13L25 19L33 7" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 9V29M8.5 13H15.5M8.5 19H15.5" stroke="#F6C85F" stroke-width="2.2" stroke-linecap="round"/></svg></div><div><div class="logo-name">TEMEXY</div><div class="logo-tag">TRADE JOURNAL</div></div></div></div>', unsafe_allow_html=True); st.sidebar.caption('Evidence over emotion • Process over outcome')
page=st.sidebar.radio('Navigate',['🏠 Dashboard','➕ New Trade','📖 Trade History','🔎 Trade Detail','📊 Analytics','📚 Setup Library','⚙️ Settings'])
st.sidebar.metric('Total Trades',len(T))
if T:
    wins=sum(x['result']=='Win' for x in T); net=sum(float(x['actual_r'] or 0) for x in T)
    st.sidebar.metric('Win Rate',f'{wins/len(T)*100:.1f}%'); st.sidebar.metric('Net R',f'{net:+.2f}R')

if page=='🏠 Dashboard':
    st.markdown('<div class="temexy-hero"><div class="hero-kicker">TEMEXY • PERFORMANCE CENTER</div><div class="hero-title">Trade with evidence. Review without emotion.</div><div class="hero-sub">Your setups, execution, risk, psychology and results — organized into one clean trading command center.</div></div>', unsafe_allow_html=True); st.markdown('<div class="section-title"><span class="section-dot"></span>Performance Snapshot</div>', unsafe_allow_html=True)
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

elif page=='➕ New Trade':
    st.title('➕ Record New Trade'); st.caption('Keep it factual. Keep it quick. Build a database you can trust.'); st.markdown('<div class="small-muted">A clean record now saves you from guessing later.</div>', unsafe_allow_html=True)
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
        data={'trade_date':td.isoformat(),'trade_time':tt.strftime('%H:%M'),'market':market,'direction':direction,'timeframe':tf,'session':session,'setup_name':setup,'setup_tags':tags,'htf_bias':bias,'entry':entry,'stop_loss':sl,'take_profit':tp,'exit_price':exitp,'planned_rr':prr,'actual_r':ar,'pnl_money':pnl,'risk_percent':riskpct,'risk_money':riskmoney,'result':result,'confidence':conf,'rule_adherence':adherence,'setup_quality':quality,'news_event':news,'market_context':context,'reason':reason,'execution':execution,'emotion_before':eb,'emotion_during':ed,'emotion_after':ea,'mistake':mistake,'lesson':lesson,'what_went_well':went,'what_to_change':change,'screenshot_before':saveimg(before,stamp+'_before'),'screenshot_setup':saveimg(setupimg,stamp+'_setup'),'screenshot_after':saveimg(after,stamp+'_after'),'created_at':datetime.now().isoformat()}
        i=add(data); st.success(f'Trade #{i} saved.'); st.balloons()

elif page=='📖 Trade History':
    st.title('📖 Complete Trade History')
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

elif page=='🔎 Trade Detail':
    st.title('🔎 Trade Detail')
    if not T: st.info('No trades yet.')
    else:
        opts={f"#{t['id']} · {t['trade_date']} · {t['market']} · {t['direction']} · {t['result']}":t['id'] for t in T}; label=st.selectbox('Select trade',list(opts)); t=get(opts[label])
        a,b,c,d,e=st.columns(5); a.metric('Result',t['result']); b.metric('R',num(t['actual_r'])); c.metric('P/L',money(t['pnl_money'])); d.metric('Planned RR',num(t['planned_rr'])); e.metric('Rules',f"{t['rule_adherence']}/10")
        l,r=st.columns(2)
        with l:
            st.subheader('📌 Trade Information'); st.write(f"**Date:** {t['trade_date']} {t['trade_time']}"); st.write(f"**Market:** {t['market']}"); st.write(f"**Direction:** {t['direction']}"); st.write(f"**Timeframe:** {t['timeframe']}"); st.write(f"**Session:** {t['session']}"); st.write(f"**Setup:** {t['setup_name']}"); st.write(f"**Tags:** {t['setup_tags']}"); st.write(f"**HTF Bias:** {t['htf_bias']}"); st.write(f"**News:** {t['news_event']}")
        with r:
            st.subheader('💰 Numbers'); st.write(f"**Entry:** {num(t['entry'])}"); st.write(f"**SL:** {num(t['stop_loss'])}"); st.write(f"**TP:** {num(t['take_profit'])}"); st.write(f"**Exit:** {num(t['exit_price'])}"); st.write(f"**Risk:** {num(t['risk_percent'])}% / {money(t['risk_money'])}"); st.write(f"**Confidence:** {t['confidence']}/10"); st.write(f"**Setup Quality:** {t['setup_quality']}/10")
        st.subheader('🖼️ Chart Record'); cols=st.columns(3)
        for col,title,k in zip(cols,['Before Entry','Setup / Entry','After Exit'],['screenshot_before','screenshot_setup','screenshot_after']):
            with col:
                st.markdown(f'**{title}**'); p=t[k]
                if p and os.path.exists(p):st.image(p,use_container_width=True)
                else:st.caption('No image.')
        for title,k in [('🧠 Why I Took It','reason'),('🌍 Market Context','market_context'),('⚙️ Execution','execution'),('😐 Before','emotion_before'),('😰 During','emotion_during'),('😌 After','emotion_after'),('✅ What Went Well','what_went_well'),('❌ Mistake','mistake'),('💡 Lesson','lesson'),('🔁 What I Will Change','what_to_change')]:
            if t[k]: st.subheader(title); st.write(t[k])
        if st.button('🗑️ Delete This Trade'): remove(t['id']); st.success('Deleted.'); st.rerun()

elif page=='📊 Analytics':
    st.title('📊 Trading Analytics'); st.caption('Let the journal show you where your performance comes from.')
    if not T: st.info('Record trades first.')
    else:
        d=pd.DataFrame(T); d['actual_r']=pd.to_numeric(d.actual_r,errors='coerce').fillna(0); d['rule_adherence']=pd.to_numeric(d.rule_adherence,errors='coerce'); d['setup_quality']=pd.to_numeric(d.setup_quality,errors='coerce'); d['confidence']=pd.to_numeric(d.confidence,errors='coerce')
        for title,col in [('By Market','market'),('By Setup','setup_name'),('By Session','session'),('By Direction','direction')]:
            st.subheader(title); g=d.groupby(col).agg(Trades=('id','count'),Net_R=('actual_r','sum'),Avg_R=('actual_r','mean'),Wins=('result',lambda x:(x=='Win').sum()),Losses=('result',lambda x:(x=='Loss').sum())).reset_index(); g['Win_Rate_%']=g.Wins/g.Trades*100; st.dataframe(g,use_container_width=True,hide_index=True)
        st.subheader('Discipline vs Result'); st.dataframe(d.groupby('result')[['rule_adherence','setup_quality','confidence']].mean(),use_container_width=True)
        st.subheader('Monthly R'); d['month']=pd.to_datetime(d.trade_date).dt.to_period('M').astype(str); st.bar_chart(d.groupby('month').actual_r.sum())

elif page=='📚 Setup Library':
    st.markdown('<div class="temexy-hero"><div class="hero-kicker">VISUAL PATTERN MEMORY</div><div class="hero-title">📚 Setup Library</div><div class="hero-sub">Upload a new chart and retrieve the closest historical formations. Your old Buy/Sell labels do not control the visual match.</div></div>', unsafe_allow_html=True)
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
    st.markdown('---'); st.subheader('Saved Setup Screenshots')
    for t in T:
        p=t.get('screenshot_setup') or t.get('screenshot_before')
        if p and os.path.exists(p):
            with st.expander(f"#{t['id']} · {t['market']} · {t['setup_name']} · {t['result']}"): st.image(p,width=700); st.write(f"{t['direction']} · {t['timeframe']} · {t['session']} · {t['actual_r']}R")

else:
    st.title('⚙️ Journal Settings')
    st.info('This journal records the complete trade lifecycle: setup, market context, numbers, execution, psychology, mistakes, lessons, and chart evidence.')
    st.subheader('Included');
    for x in ['Trade date/time','Market, direction, timeframe and session','Setup name and tags','HTF bias','Entry, SL, TP and exit','Planned RR, actual R, risk % and money','Win/Loss/BE','Confidence, setup quality and rule adherence','News and market context','Reason for entry and execution notes','Before/during/after emotions','Mistakes, lessons and next change','Before/setup/after screenshots','Visual setup similarity search','Market/setup/session/direction analytics','Equity curve and monthly performance']:
        st.write('✅ '+x)
    st.warning('Important for Streamlit Cloud: this version stores the SQLite database and screenshots in the app filesystem. For a permanent cloud journal, connect persistent storage/database before building a large archive.')
    st.code(str(BASE))

st.markdown('---'); st.caption('TEMEXY TRADE JOURNAL • Evidence over emotion • Process over outcome')
