import os
import streamlit as st
from openai import OpenAI
import math
import re
import pandas as pd

# Public portfolio build: no paid/external API calls are made.
DEMO_MODE = True
from dotenv import load_dotenv
from supabase import create_client
from product_analyser import analyse_product
from market_discovery import discover_market
from people_discovery import hunter_is_configured, find_people_for_companies

# ============================================================
# REACH — COMPLETE STORYBOARD UI
# Designed from the approved 9-screen REACH reference.
# Real product analysis + real Companies House discovery retained.
# ============================================================

st.set_page_config(
    page_title="REACH — Turn your market green",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# REQUIRED SESSION STATE — initialise before any page uses it
# ============================================================
_COMPANY_STATE_DEFAULTS = {
    "company_view_mode": "Default",
    "company_status_filter": "All companies",
    "selected_company_index": None,
    "selected_company_record": None,
    "show_company_filters": False,
    "user_location_label": "",
    "user_location_coords": None,
    "distance_radius_miles": "Anywhere",
}

for _state_key, _state_default in _COMPANY_STATE_DEFAULTS.items():
    if _state_key not in st.session_state:
        st.session_state[_state_key] = _state_default


# ============================================================
# SESSION STATE
# ============================================================

DEFAULTS = {
    "page": "Landing",
    "analysis": None,
    "product_description": "",
    "selected_location": "United Kingdom",
    "website": "",
    "market_results": [],
    "market_built": False,
    "market_visible_count": 10,
    "strategy_editing": False,
    "strategy_saved_message": False,
    "auth_user": None,
    "auth_email": "",
    "workspace_id": None,
    "workspace_name": "",
    "supabase_access_token": None,
    "supabase_refresh_token": None,
    "auth_mode": "Sign in",
    "post_auth_page": "Home",
    "product_id": None,
    "strategy_id": None,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ============================================================
# GLOBAL CSS — MATCHES THE APPROVED REFERENCE
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root{
    --bg:#020806;
    --bg2:#04100a;
    --panel:#06120c;
    --panel2:#07170f;
    --panel3:#0a1c13;
    --line:#12301e;
    --line2:rgba(255,255,255,.075);
    --green:#2df58a;
    --green2:#1fd876;
    --green-soft:rgba(45,245,138,.10);
    --text:#f3f8f5;
    --muted:#708077;
    --muted2:#536259;
    --blue:#43a9ff;
    --yellow:#f4c84d;
    --orange:#ff9f43;
    --red:#ff6767;
}

*{box-sizing:border-box}
html,body,[class*="css"]{
    font-family:'Inter',sans-serif!important;
}
.stApp{
    background:
      radial-gradient(circle at 10% 0%,rgba(45,245,138,.07),transparent 26%),
      radial-gradient(circle at 92% 22%,rgba(45,245,138,.045),transparent 24%),
      #020806!important;
    color:var(--text)!important;
}
header[data-testid="stHeader"]{
    background:transparent!important;
    height:0!important;
}
#MainMenu,footer{visibility:hidden}
.block-container{
    max-width:1500px!important;
    padding-top:1.1rem!important;
    padding-bottom:4rem!important;
}
h1,h2,h3,h4,p,label{color:var(--text)!important}
[data-testid="stCaptionContainer"]{color:var(--muted)!important}

/* SIDEBAR */
section[data-testid="stSidebar"]{
    background:
      radial-gradient(circle at 10% 8%,rgba(45,245,138,.055),transparent 28%),
      #030b07!important;
    border-right:1px solid rgba(45,245,138,.10)!important;
    min-width:218px!important;
    max-width:218px!important;
}
section[data-testid="stSidebar"]>div{
    padding-top:14px!important;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p{
    margin:0!important;
}
.side-logo{
    font-size:18px;
    font-weight:800;
    letter-spacing:-.5px;
    padding:6px 5px 14px;
}
.side-logo .dot{color:var(--green)}
.side-label{
    color:#4f6157;
    font-size:7px;
    letter-spacing:1.35px;
    font-weight:800;
    margin:15px 5px 5px;
}
.side-market{
    margin-top:22px;
    padding:12px;
    border:1px solid rgba(45,245,138,.18);
    background:linear-gradient(145deg,rgba(45,245,138,.07),rgba(4,15,9,.92));
    border-radius:10px;
}
.side-market b{font-size:8px}
.side-market p{font-size:7px;color:#617168;margin:5px 0 8px!important}
.side-track{height:4px;background:#13251a;border-radius:99px;overflow:hidden}
.side-track i{display:block;width:35%;height:100%;background:var(--green)}

section[data-testid="stSidebar"] .stButton>button{
    width:100%;
    justify-content:flex-start;
    text-align:left;
    min-height:34px!important;
    padding:0 10px!important;
    margin:1px 0!important;
    border:1px solid transparent!important;
    background:transparent!important;
    color:#829087!important;
    border-radius:7px!important;
    font-size:8px!important;
    font-weight:500!important;
    box-shadow:none!important;
}
section[data-testid="stSidebar"] .stButton>button:hover{
    background:rgba(45,245,138,.055)!important;
    color:#e9f7ef!important;
}
section[data-testid="stSidebar"] .stButton>button[kind="primary"]{
    background:rgba(45,245,138,.11)!important;
    border-color:rgba(45,245,138,.16)!important;
    color:#49f49a!important;
}

/* NATIVE CONTROLS */
.stButton>button{
    border-radius:8px!important;
    border:1px solid var(--line2)!important;
    background:#07130d!important;
    color:#d7e2dc!important;
    font-size:9px!important;
    font-weight:700!important;
    min-height:38px!important;
}
.stButton>button:hover{
    border-color:rgba(45,245,138,.35)!important;
    color:var(--green)!important;
}
.stButton>button[kind="primary"]{
    background:var(--green)!important;
    border-color:var(--green)!important;
    color:#011108!important;
    font-weight:800!important;
    box-shadow:0 8px 30px rgba(45,245,138,.12)!important;
}
.stButton>button[kind="primary"]:hover{
    background:#57f7a2!important;
    color:#011108!important;
}
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-baseweb="select"]>div{
    background:#06120c!important;
    border:1px solid rgba(255,255,255,.085)!important;
    color:#eef7f2!important;
    border-radius:8px!important;
    font-size:10px!important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus{
    border-color:rgba(45,245,138,.55)!important;
    box-shadow:0 0 0 2px rgba(45,245,138,.06)!important;
}
[data-testid="stExpander"]{
    background:#06120c!important;
    border:1px solid rgba(255,255,255,.07)!important;
    border-radius:9px!important;
}
div[data-testid="stMetric"]{
    background:#06120c!important;
    border:1px solid rgba(255,255,255,.07)!important;
    border-radius:10px!important;
    padding:13px!important;
}
hr{border-color:rgba(255,255,255,.06)!important}

/* LANDING */
.landing-nav{
    height:64px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    border-bottom:1px solid rgba(255,255,255,.05);
    margin-top:-18px;
}
.brand{
    font-size:17px;
    font-weight:800;
    letter-spacing:-.5px;
}
.brand .dot,.green{color:var(--green)}
.landing-links{
    display:flex;
    gap:28px;
    color:#78887e;
    font-size:8px;
}
.nav-actions{display:flex;gap:9px;align-items:center}
.nav-sign{font-size:8px;color:#819087}
.nav-cta{
    background:var(--green);
    color:#011108;
    padding:9px 13px;
    border-radius:7px;
    font-size:8px;
    font-weight:800;
}

/* PREMIUM LANDING MARKET SEARCH */
.market-entry-card{
    width:min(100%,980px);
    margin:22px auto 0;
    padding:26px 28px 20px;
    border:1px solid rgba(46,234,122,.30);
    border-radius:22px 22px 8px 8px;
    background:
      radial-gradient(circle at 18% 0%,rgba(46,234,122,.08),transparent 36%),
      linear-gradient(180deg,rgba(8,27,17,.96),rgba(3,13,8,.98));
    box-shadow:0 24px 65px rgba(0,0,0,.28);
}
.market-entry-top{
    display:grid;
    grid-template-columns:minmax(0,1fr) minmax(0,1.35fr);
    gap:34px;
    align-items:center;
}
.market-entry-copy{
    padding-right:28px;
    border-right:1px solid rgba(46,234,122,.18);
}
.market-entry-eyebrow{
    display:flex;
    align-items:center;
    gap:8px;
    color:#43F297;
    font-size:10px;
    font-weight:850;
    letter-spacing:.22em;
    margin-bottom:15px;
}
.market-entry-eyebrow span{
    width:7px;height:7px;border-radius:50%;background:#2EEA7A;
    box-shadow:0 0 16px rgba(46,234,122,.55);
}
.market-entry-title{
    color:#F2F8F4;
    font-size:27px;
    line-height:1.12;
    font-weight:760;
    letter-spacing:-.03em;
}
.market-entry-title b{color:#2EEA7A;font-weight:800}
.market-entry-benefits{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:12px 18px;
}
.market-benefit{
    display:flex;align-items:center;gap:12px;min-width:0;
}
.market-benefit:first-child{grid-row:span 2}
.market-benefit-icon{
    flex:0 0 42px;height:42px;border-radius:11px;
    display:grid;place-items:center;
    color:#2EEA7A;font-size:20px;
    background:rgba(46,234,122,.08);
    border:1px solid rgba(46,234,122,.13);
}
.market-benefit strong{
    display:block;color:#EEF8F1;font-size:12px;line-height:1.25;margin-bottom:4px;
}
.market-benefit small{
    display:block;color:#809489;font-size:10px;line-height:1.35;
}

/* Pull the real Streamlit search controls into one premium panel. */
div[data-testid="stForm"]{
    width:min(100%,980px) !important;
    margin:0 auto 26px !important;
    padding:10px 28px 22px !important;
    background:linear-gradient(180deg,rgba(3,13,8,.98),rgba(4,17,10,.98)) !important;
    border:1px solid rgba(46,234,122,.30) !important;
    border-top:0 !important;
    border-radius:8px 8px 22px 22px !important;
    box-shadow:0 24px 65px rgba(0,0,0,.28) !important;
}
div[data-testid="stForm"] [data-testid="stWidgetLabel"] p{
    color:#EAF4EE !important;font-size:12px !important;font-weight:700 !important;
}
div[data-testid="stForm"] .stTextArea textarea{
    min-height:74px !important;
    background:#07150E !important;
    border:1px solid rgba(222,255,235,.45) !important;
    border-radius:12px !important;
    color:#F2F8F4 !important;
    font-size:13px !important;
    padding:15px 16px !important;
}
div[data-testid="stForm"] .stTextArea textarea:focus{
    border-color:#2EEA7A !important;
    box-shadow:0 0 0 2px rgba(46,234,122,.10) !important;
}
div[data-testid="stForm"] .stTextInput div[data-baseweb="input"],
div[data-testid="stForm"] div[data-baseweb="select"] > div{
    min-height:46px !important;
    border-radius:11px !important;
    background:#07150E !important;
    border-color:rgba(222,255,235,.28) !important;
}
div[data-testid="stForm"] button[kind="primaryFormSubmit"],
div[data-testid="stForm"] .stFormSubmitButton button{
    min-height:48px !important;
    border-radius:11px !important;
    background:linear-gradient(90deg,#36F093,#2EEA7A) !important;
    border:0 !important;
    color:#031109 !important;
    font-weight:850 !important;
    box-shadow:0 12px 28px rgba(46,234,122,.14) !important;
}
div[data-testid="stForm"] .stFormSubmitButton button:hover{
    transform:translateY(-1px);
    box-shadow:0 15px 34px rgba(46,234,122,.22) !important;
}
@media(max-width:820px){
    .market-entry-card{padding:22px 20px 16px}
    .market-entry-top{grid-template-columns:1fr;gap:20px}
    .market-entry-copy{padding-right:0;border-right:0}
    .market-entry-benefits{grid-template-columns:1fr}
    .market-benefit:first-child{grid-row:auto}
    div[data-testid="stForm"]{padding:8px 20px 20px !important}
}

.landing-hero{
    position:relative;
    text-align:center;
    min-height:calc(100vh - 64px);
    box-sizing:border-box;
    padding:42px 20px 56px;
    overflow:hidden;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
}
.landing-hero:before{
    content:"";
    position:absolute;
    width:760px;height:500px;
    left:50%;top:-120px;
    transform:translateX(-50%);
    background:radial-gradient(ellipse,rgba(45,245,138,.12),transparent 65%);
    pointer-events:none;
}
.eyebrow-pill{
    display:inline-block;
    position:relative;
    border:1px solid rgba(45,245,138,.22);
    background:rgba(45,245,138,.055);
    color:#54f6a0;
    padding:6px 10px;
    border-radius:99px;
    font-size:7px;
    letter-spacing:1.2px;
    font-weight:800;
}
.landing-hero h1{
    position:relative;
    font-size:58px;
    line-height:1.02;
    letter-spacing:-3.3px;
    margin:19px auto 15px;
    max-width:900px;
    font-weight:800;
}
.landing-hero p{
    position:relative;
    max-width:650px;
    margin:auto;
    color:#7b8a81!important;
    font-size:10px;
    line-height:1.7;
}
.hero-actions{
    position:relative;
    margin:23px auto 0;
    display:flex;
    justify-content:center;
    gap:9px;
}
.hero-primary,.hero-secondary{
    padding:11px 17px;
    border-radius:8px;
    font-size:8px;
    font-weight:800;
}
.hero-primary{background:var(--green);color:#011108}
.hero-secondary{border:1px solid var(--line2);background:#06120c;color:#a8b5ad}

@media(max-height:760px){
    .landing-hero{
        min-height:auto;
        padding-top:70px;
        padding-bottom:54px;
    }
}
@media(max-width:820px){
    .landing-hero{
        min-height:calc(100vh - 64px);
        padding-top:42px;
        padding-bottom:48px;
    }
}
.hero-demo{
    position:relative;
    max-width:880px;
    margin:46px auto 0;
    border:1px solid rgba(45,245,138,.17);
    border-radius:13px;
    overflow:hidden;
    background:#04100a;
    box-shadow:0 30px 100px rgba(0,0,0,.42),0 0 60px rgba(45,245,138,.045);
    text-align:left;
}
.demo-bar{
    height:38px;
    border-bottom:1px solid rgba(255,255,255,.06);
    display:flex;
    align-items:center;
    padding:0 11px;
}
.demo-dot{width:6px;height:6px;border-radius:50%;background:#21352a;margin-right:4px}
.demo-dot.g{background:var(--green)}
.demo-grid{display:grid;grid-template-columns:145px 1fr;min-height:315px}
.demo-side{border-right:1px solid rgba(255,255,255,.06);padding:11px;background:#050f09}
.demo-side div{font-size:7px;color:#67776d;padding:7px 8px;border-radius:6px}
.demo-side div:first-child{background:rgba(45,245,138,.09);color:#45ee94}
.demo-content{padding:17px}
.demo-title{font-size:14px;font-weight:800}
.demo-caption{font-size:6px;color:#64746a;margin-top:3px}
.demo-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;margin:13px 0}
.demo-card{padding:10px;border:1px solid rgba(255,255,255,.065);border-radius:8px;background:#06120c}
.demo-card b{font-size:16px;display:block}
.demo-card span{font-size:6px;color:#65746a}
.demo-card.blue b{color:var(--blue)}
.demo-card.yellow b{color:var(--yellow)}
.demo-card.green b{color:var(--green)}
.demo-progress{padding:10px;border:1px solid rgba(255,255,255,.065);border-radius:8px;background:#06120c}
.demo-progress b{font-size:7px}.demo-progress em{float:right;color:var(--green);font-size:7px;font-style:normal}
.demo-track{height:4px;background:#13251a;border-radius:99px;margin-top:7px;overflow:hidden}
.demo-track i{display:block;width:38%;height:100%;background:var(--green)}
.demo-table{margin-top:9px;border:1px solid rgba(255,255,255,.06);border-radius:8px;overflow:hidden}
.demo-row{display:grid;grid-template-columns:1.4fr .7fr .45fr;padding:8px 9px;border-top:1px solid rgba(255,255,255,.045);font-size:6px;color:#7d8b82}
.demo-row:first-child{border-top:0;color:#526158}

/* APP TOP */
.app-top{
    height:50px;
    display:grid;
    grid-template-columns:minmax(300px,620px) auto;
    align-items:center;
    gap:18px;
    margin-bottom:17px;
}
.global-search{
    height:36px;
    border:1px solid rgba(255,255,255,.075);
    border-radius:8px;
    background:#06120c;
    display:flex;
    align-items:center;
    padding:0 11px;
    color:#718078;
    font-size:8px;
}
.global-search span{margin-left:auto;color:#44534a}
.top-icons{display:flex;gap:6px;justify-content:flex-end}
.top-icon{
    width:33px;height:33px;
    display:grid;place-items:center;
    border:1px solid rgba(255,255,255,.07);
    background:#06120c;
    border-radius:8px;
    color:#718078;
    font-size:8px;
}
.top-icon.user{color:#3ff194}

/* COMMON APP */
.page-eyebrow{
    color:#45ef95;
    font-size:7px;
    font-weight:800;
    letter-spacing:1.25px;
    margin-bottom:5px;
}
.page-title{
    font-size:24px;
    line-height:1.1;
    letter-spacing:-1px;
    font-weight:800;
}
.page-sub{
    color:#74837a;
    font-size:8px;
    margin-top:6px;
}
.surface{
    background:
      radial-gradient(circle at 100% 0%,rgba(45,245,138,.045),transparent 28%),
      #06120c;
    border:1px solid rgba(255,255,255,.07);
    border-radius:10px;
}
.market-heading{
    margin-top:13px;
    padding:14px 16px;
    border:1px solid rgba(45,245,138,.17);
    border-radius:10px;
    background:linear-gradient(135deg,rgba(45,245,138,.055),#06120c);
}
.market-heading b{font-size:12px}
.market-heading p{font-size:7px;color:#68786e!important;margin:4px 0 0!important}
.metrics4{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:8px;
    margin:12px 0;
}
.metricbox{
    padding:13px;
    background:#06120c;
    border:1px solid rgba(255,255,255,.07);
    border-radius:9px;
}
.metricbox b{display:block;font-size:20px;letter-spacing:-.8px}
.metricbox span{font-size:7px;color:#65746a}
.metricbox.blue b{color:var(--blue)}
.metricbox.yellow b{color:var(--yellow)}
.metricbox.green b{color:var(--green)}

.toolbar{
    display:flex;
    align-items:center;
    gap:6px;
    flex-wrap:wrap;
    margin:11px 0 8px;
}
.tool{
    padding:7px 9px;
    border:1px solid rgba(255,255,255,.07);
    background:#06120c;
    border-radius:7px;
    color:#87958c;
    font-size:7px;
}
.tool.ai{color:#47f098;border-color:rgba(45,245,138,.18)}
.tool.push{margin-left:auto}

.status-tabs{
    display:flex;
    gap:6px;
    margin:10px 0;
}
.status-tab{
    border:1px solid rgba(255,255,255,.07);
    background:#06120c;
    color:#78877e;
    border-radius:99px;
    padding:6px 9px;
    font-size:7px;
}
.status-tab.on{
    color:#43ef94;
    border-color:rgba(45,245,138,.18);
    background:rgba(45,245,138,.07);
}

/* ANALYSING */
.analyse-wrap{
    min-height:65vh;
    display:grid;
    place-items:center;
}
.analyse-card{
    width:min(650px,100%);
    padding:26px;
    border:1px solid rgba(45,245,138,.16);
    background:
      radial-gradient(circle at 50% 0%,rgba(45,245,138,.10),transparent 36%),
      #06120c;
    border-radius:12px;
}
.analyse-icon{
    width:42px;height:42px;
    border-radius:50%;
    display:grid;place-items:center;
    margin:0 auto 14px;
    border:1px solid rgba(45,245,138,.28);
    color:var(--green);
    box-shadow:0 0 35px rgba(45,245,138,.10);
}
.analyse-card h2{text-align:center;font-size:21px;margin:0 0 5px}
.analyse-card>p{text-align:center;color:#6e7d74!important;font-size:8px}
.check-list{margin-top:20px}
.check-line{
    display:flex;align-items:center;gap:9px;
    padding:9px 0;
    border-bottom:1px solid rgba(255,255,255,.045);
    font-size:8px;color:#aab6af;
}
.tick{
    width:18px;height:18px;border-radius:50%;
    display:grid;place-items:center;
    background:rgba(45,245,138,.10);
    color:var(--green);
    font-size:7px;
}
.analyse-track{height:5px;background:#13251a;border-radius:99px;margin-top:17px;overflow:hidden}
.analyse-track i{display:block;width:82%;height:100%;background:linear-gradient(90deg,var(--green2),var(--green))}

/* MARKET READY */
.ready-layout{
    display:grid;
    grid-template-columns:1.45fr .75fr;
    gap:10px;
    margin-top:12px;
}
.overview-card{padding:15px}
.overview-card h3{font-size:11px;margin:0 0 10px}
.overview-row{
    display:flex;justify-content:space-between;
    padding:8px 0;
    border-top:1px solid rgba(255,255,255,.045);
    font-size:7px;
}
.overview-row span:first-child{color:#65746a}
.score-card{padding:15px;text-align:center}
.score-ring{
    width:78px;height:78px;border-radius:50%;
    margin:10px auto;
    display:grid;place-items:center;
    background:conic-gradient(var(--green) 0 84%,#13251a 84%);
    position:relative;
}
.score-ring:after{
    content:"";position:absolute;inset:7px;border-radius:50%;background:#06120c
}
.score-ring b{position:relative;z-index:2;font-size:18px}

/* TABLE */
.table-shell{
    border:1px solid rgba(255,255,255,.07);
    border-radius:9px;
    overflow:hidden;
    background:#06120c;
}
.company-head,.company-row{
    display:grid;
    grid-template-columns:28px 1.55fr .85fr .95fr .75fr .65fr;
    min-width:760px;
    align-items:center;
}
.company-head{
    background:#07170f;
    color:#526158;
    font-size:6px;
    text-transform:uppercase;
    letter-spacing:.4px;
}
.company-row{
    border-top:1px solid rgba(255,255,255,.045);
    color:#8d9a92;
    font-size:7px;
}
.company-head>div,.company-row>div{padding:9px 8px}
.company-row strong{color:#e8f1ec;font-size:8px}
.company-row small{display:block;color:#526158;font-size:6px;margin-top:2px}
.checkbox{
    width:12px;height:12px;border:1px solid #34473b;border-radius:3px;
}
.tag{
    display:inline-block;
    padding:4px 6px;
    border-radius:99px;
    font-size:6px;
    border:1px solid rgba(255,255,255,.07);
}
.tag.discovered{color:#a6b2aa}
.tag.verified{color:var(--blue);background:rgba(67,169,255,.07)}
.tag.contacted{color:var(--yellow);background:rgba(244,200,77,.07)}
.tag.interested{color:var(--green);background:rgba(45,245,138,.08)}
.match{color:var(--green);font-weight:700}

/* PEOPLE */
.people-layout{
    display:grid;
    grid-template-columns:205px minmax(0,1fr);
    min-height:510px;
    border:1px solid rgba(255,255,255,.07);
    border-radius:9px;
    overflow:hidden;
    margin-top:9px;
}
.filters{
    background:#06120c;
    border-right:1px solid rgba(255,255,255,.06);
}
.filter-tabs{display:grid;grid-template-columns:repeat(3,1fr);border-bottom:1px solid rgba(255,255,255,.06)}
.filter-tab{text-align:center;padding:9px 3px;color:#637269;font-size:6px}
.filter-tab b{display:block;color:#dce7e0;font-size:10px}
.filter-tab.on{background:rgba(45,245,138,.055);color:#48ef97}
.filter-line{
    display:flex;justify-content:space-between;
    padding:11px 10px;
    border-bottom:1px solid rgba(255,255,255,.04);
    color:#909d95;
    font-size:7px;
}
.filter-line.ai{color:#47ef97}
.people-results{background:#04100a;overflow:auto}
.people-head,.people-row{
    display:grid;
    grid-template-columns:28px 1.15fr 1fr 1fr .9fr .6fr;
    min-width:720px;
    align-items:center;
}
.people-head{background:#06120c;color:#526158;text-transform:uppercase;font-size:6px}
.people-head>div,.people-row>div{padding:9px 8px}
.people-row{border-top:1px solid rgba(255,255,255,.045);font-size:7px;color:#8c9991}
.people-row strong{color:#e7f0eb}
.people-empty{text-align:center;padding:80px 20px;color:#64736a;font-size:7px}
.people-empty b{display:block;color:#dce7e0;font-size:11px;margin-bottom:5px}

/* OUTREACH */
.outreach-layout{
    display:grid;
    grid-template-columns:1.3fr .7fr;
    gap:10px;
    margin-top:12px;
}
.sequence{padding:15px}
.sequence h3{font-size:11px;margin:0}
.sequence>p{font-size:7px;color:#68776e!important}
.seq-line{
    display:grid;
    grid-template-columns:46px 28px 1fr 85px;
    align-items:center;
    gap:8px;
    padding:10px 0;
    border-top:1px solid rgba(255,255,255,.045);
}
.seq-day{font-size:7px;color:#66756c}
.seq-icon{
    width:26px;height:26px;border-radius:7px;
    display:grid;place-items:center;
    background:rgba(45,245,138,.07);
    color:#44ef95;
    font-size:8px;
}
.seq-copy b{display:block;font-size:8px}
.seq-copy span{font-size:6px;color:#607067}
.seq-state{
    border:1px solid rgba(255,255,255,.07);
    border-radius:6px;
    padding:6px;
    text-align:center;
    font-size:6px;
    color:#87948c;
}
.coming{padding:17px}
.coming-badge{
    display:inline-block;
    padding:5px 7px;
    border-radius:99px;
    background:rgba(45,245,138,.08);
    color:#46f097;
    font-size:6px;
    font-weight:800;
}
.coming h3{font-size:13px;margin:11px 0 6px}
.coming p{font-size:7px;color:#69786f!important;line-height:1.6}

/* ANALYTICS */
.pipeline{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:8px;
    margin:12px 0;
}
.pipeline-card{
    padding:13px;
    border:1px solid rgba(255,255,255,.07);
    background:#06120c;
    border-radius:9px;
}
.pipeline-card b{font-size:20px;display:block}
.pipeline-card span{font-size:7px;color:#65746a}
.chart{
    padding:15px;
    margin-top:10px;
}
.chart-head{display:flex;justify-content:space-between}
.chart-head b{font-size:10px}
.chart-head span{font-size:7px;color:#65746a}
.bars{
    height:150px;
    display:flex;
    align-items:flex-end;
    gap:10px;
    padding:15px 5px 4px;
    border-bottom:1px solid rgba(255,255,255,.06);
}
.bar{
    flex:1;
    min-width:10px;
    border-radius:4px 4px 0 0;
    background:linear-gradient(180deg,#38ef8d,#0b5d32);
    box-shadow:0 0 20px rgba(45,245,138,.05);
}
.bar-labels{
    display:grid;
    grid-template-columns:repeat(8,1fr);
    gap:10px;
    text-align:center;
    color:#526158;
    font-size:6px;
    padding-top:6px;
}

/* CLOSING */
.closing{
    min-height:70vh;
    display:grid;
    place-items:center;
    text-align:center;
}
.closing-inner{max-width:680px}
.closing-globe{
    width:170px;height:170px;
    margin:0 auto 18px;
    border-radius:50%;
    border:1px solid rgba(45,245,138,.22);
    background:
      radial-gradient(circle at 38% 35%,rgba(45,245,138,.28),transparent 8%),
      radial-gradient(circle at 63% 50%,rgba(45,245,138,.22),transparent 7%),
      radial-gradient(circle at 47% 67%,rgba(45,245,138,.25),transparent 6%),
      radial-gradient(circle,rgba(45,245,138,.13),rgba(45,245,138,.02) 55%,transparent 70%);
    box-shadow:0 0 80px rgba(45,245,138,.11);
    position:relative;
}
.closing-globe:before,.closing-globe:after{
    content:"";position:absolute;border:1px solid rgba(45,245,138,.12);border-radius:50%
}
.closing-globe:before{inset:25px -25px}
.closing-globe:after{inset:-25px 25px}
.closing h1{font-size:42px;letter-spacing:-2px;margin:0}
.closing p{font-size:9px;color:#718078!important}
.closing-brand{margin-top:22px;font-size:10px;font-weight:800}

/* MOBILE */
@media(max-width:950px){
    .landing-links{display:none}
    .landing-hero h1{font-size:42px;letter-spacing:-2px}
    .demo-grid{grid-template-columns:1fr}.demo-side{display:none}
    .metrics4,.pipeline{grid-template-columns:1fr 1fr}
    .ready-layout,.outreach-layout{grid-template-columns:1fr}
    .people-layout{grid-template-columns:1fr}.filters{display:none}
}

/* ============================================================
   READABILITY OVERRIDE — larger type without changing layout
   ============================================================ */
.page-eyebrow{font-size:9px!important;letter-spacing:1.15px!important}
.page-title{font-size:28px!important}
.page-sub{font-size:10px!important;line-height:1.55!important;color:#8c9b92!important}

.global-search{font-size:10px!important}
.top-icon{font-size:10px!important}

section[data-testid="stSidebar"] .stButton>button{
    font-size:10px!important;
    min-height:38px!important;
}
.side-label{font-size:8px!important}
.side-market b{font-size:10px!important}
.side-market p{font-size:8px!important}

.toolbar .tool{font-size:9px!important;padding:8px 10px!important}
.status-tab{font-size:9px!important}

.outreach-layout{grid-template-columns:minmax(0,1.55fr) minmax(290px,.65fr)!important}
.sequence{padding:20px!important}
.sequence h3{font-size:14px!important}
.sequence>p{font-size:9px!important;line-height:1.5!important;color:#87968d!important}
.seq-line{
    grid-template-columns:58px 34px minmax(0,1fr) 100px!important;
    gap:11px!important;
    padding:15px 0!important;
}
.seq-day{font-size:9px!important;color:#87968d!important}
.seq-icon{width:31px!important;height:31px!important;font-size:10px!important}
.seq-copy b{font-size:11px!important;line-height:1.35!important}
.seq-copy span{font-size:8.5px!important;line-height:1.5!important;color:#819087!important}
.seq-state{font-size:8px!important;padding:7px!important}

.coming{padding:21px!important}
.coming-badge{font-size:8px!important;padding:6px 8px!important}
.coming h3{font-size:16px!important}
.coming p{font-size:9px!important;line-height:1.65!important;color:#839188!important}
.coming div{font-size:8.5px!important;line-height:1.6!important}

.company-head{font-size:8px!important}
.company-row{font-size:9px!important}
.company-row strong{font-size:10px!important}
.company-row small{font-size:8px!important}
.tag{font-size:8px!important}
.people-head{font-size:8px!important}
.people-row{font-size:9px!important}
.filter-line{font-size:9px!important}
.people-empty{font-size:9px!important}
.people-empty b{font-size:13px!important}

.metricbox span,.pipeline-card span{font-size:9px!important}
.overview-row{font-size:9px!important}
.market-heading p{font-size:9px!important}

@media(max-width:1100px){
    .outreach-layout{grid-template-columns:1fr!important}
}


/* ============================================================
   REACH LARGE READABLE TYPE — desktop readability pass
   ============================================================ */
html, body, [class*="css"], .stApp{
    font-size:16px!important;
}

/* Main page headings */
.page-eyebrow{
    font-size:12px!important;
    line-height:1.4!important;
}
.page-title{
    font-size:34px!important;
    line-height:1.15!important;
}
.page-sub{
    font-size:14px!important;
    line-height:1.6!important;
    color:#9aa8a0!important;
}

/* Sidebar */
.side-logo{font-size:21px!important}
.side-label{
    font-size:10px!important;
    line-height:1.4!important;
    margin-top:20px!important;
}
section[data-testid="stSidebar"] .stButton>button{
    font-size:14px!important;
    min-height:44px!important;
    padding:0 13px!important;
}
.side-market b{font-size:13px!important}
.side-market p{font-size:11px!important}

/* Top search / controls */
.global-search{
    font-size:12px!important;
    height:42px!important;
}
.top-icon{
    width:38px!important;
    height:38px!important;
    font-size:12px!important;
}


/* GLOBAL READABILITY FIXES
   Keep text, placeholders, dropdowns and hover tooltips readable throughout REACH. */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea{
    color:#EAF4EE !important;
    -webkit-text-fill-color:#EAF4EE !important;
    caret-color:#2EEA7A !important;
    opacity:1 !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder,
div[data-baseweb="input"] input::placeholder,
div[data-baseweb="textarea"] textarea::placeholder{
    color:#91A69A !important;
    -webkit-text-fill-color:#91A69A !important;
    opacity:1 !important;
}

/* Search fields should be especially clear on the dark background. */
.stTextInput div[data-baseweb="input"]{
    background:#06120C !important;
    border-color:rgba(219,255,233,.48) !important;
}
.stTextInput div[data-baseweb="input"]:focus-within{
    border-color:#2EEA7A !important;
    box-shadow:0 0 0 1px rgba(46,234,122,.25) !important;
}

/* Select boxes / multiselects / popovers. */
div[data-baseweb="select"] > div{
    background:#06120C !important;
    color:#EAF4EE !important;
    border-color:rgba(219,255,233,.24) !important;
}
div[data-baseweb="select"] span,
div[data-baseweb="select"] input{
    color:#EAF4EE !important;
    -webkit-text-fill-color:#EAF4EE !important;
}
div[data-baseweb="popover"] > div,
div[data-baseweb="menu"],
ul[role="listbox"]{
    background:#07150E !important;
    color:#EAF4EE !important;
}
li[role="option"],
div[role="option"]{
    color:#EAF4EE !important;
}
li[role="option"]:hover,
div[role="option"]:hover{
    background:#0D2A1B !important;
}

/* Streamlit hover help / tooltips for icon buttons. */
div[data-baseweb="tooltip"],
div[role="tooltip"],
[data-testid="stTooltipContent"]{
    background:#10261A !important;
    color:#F4FFF8 !important;
    border:1px solid rgba(46,234,122,.45) !important;
    border-radius:7px !important;
    box-shadow:0 8px 24px rgba(0,0,0,.35) !important;
}
div[data-baseweb="tooltip"] *,
div[role="tooltip"] *,
[data-testid="stTooltipContent"] *{
    color:#F4FFF8 !important;
    opacity:1 !important;
}

/* General form labels/help text. */
.stTextInput label,
.stTextArea label,
.stSelectbox label,
.stMultiSelect label,
.stNumberInput label,
.stCheckbox label,
.stRadio label{
    color:#D8E8DE !important;
}
[data-testid="stWidgetLabel"] p,
[data-testid="stCaptionContainer"]{
    color:#AFC2B6 !important;
}

/* Top action buttons: icons/text remain visible at rest and on hover. */
div[data-testid="stHorizontalBlock"] .stButton > button{
    color:#EAF4EE !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button:hover{
    color:#FFFFFF !important;
    border-color:#2EEA7A !important;
    background:#0B2417 !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button p{
    color:inherit !important;
}

/* Disabled controls should still be legible. */
button:disabled,
input:disabled,
textarea:disabled{
    opacity:.62 !important;
}

/* Market ready screen */
.metricbox{
    min-height:108px!important;
    padding:18px!important;
}
.metricbox b{
    font-size:26px!important;
    line-height:1.2!important;
}
.metricbox span{
    font-size:12px!important;
    line-height:1.5!important;
}
.market-heading{
    padding:19px 20px!important;
}
.market-heading b{
    font-size:16px!important;
}
.market-heading p{
    font-size:12px!important;
    line-height:1.6!important;
}
.overview-card{
    padding:19px!important;
}
.overview-card h3{
    font-size:15px!important;
}
.overview-row{
    font-size:12px!important;
    padding:12px 0!important;
}
.score-card{
    padding:20px!important;
}
.score-card .page-eyebrow{font-size:10px!important}
.score-card div{
    font-size:12px;
}

/* Streamlit expanders and content */
[data-testid="stExpander"] summary{
    font-size:13px!important;
    min-height:48px!important;
}
[data-testid="stExpanderDetails"]{
    font-size:13px!important;
}
[data-testid="stExpanderDetails"] p,
[data-testid="stExpanderDetails"] li{
    font-size:13px!important;
    line-height:1.65!important;
}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li{
    font-size:13px;
    line-height:1.6;
}

/* Inputs */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-baseweb="select"]>div{
    font-size:13px!important;
}
.stButton>button{
    font-size:12px!important;
    min-height:42px!important;
}

/* Companies */
.toolbar .tool{
    font-size:11px!important;
    padding:9px 11px!important;
}
.status-tab{
    font-size:11px!important;
    padding:8px 11px!important;
}
.company-head{
    font-size:10px!important;
}
.company-row{
    font-size:12px!important;
}
.company-head>div,.company-row>div{
    padding:12px 10px!important;
}
.company-row strong{
    font-size:13px!important;
}
.company-row small{
    font-size:10px!important;
}
.tag{
    font-size:10px!important;
    padding:5px 8px!important;
}

/* People */
.filter-tab{font-size:10px!important}
.filter-tab b{font-size:14px!important}
.filter-line{
    font-size:12px!important;
    padding:14px 12px!important;
}
.people-head{
    font-size:10px!important;
}
.people-row{
    font-size:12px!important;
}
.people-head>div,.people-row>div{
    padding:12px 10px!important;
}
.people-empty{
    font-size:12px!important;
    line-height:1.65!important;
}
.people-empty b{
    font-size:16px!important;
}

/* Outreach */
.sequence{
    padding:23px!important;
}
.sequence h3{
    font-size:17px!important;
}
.sequence>p{
    font-size:12px!important;
    line-height:1.6!important;
}
.seq-line{
    grid-template-columns:66px 38px minmax(0,1fr) 108px!important;
    gap:13px!important;
    padding:17px 0!important;
}
.seq-day{
    font-size:11px!important;
}
.seq-icon{
    width:34px!important;
    height:34px!important;
    font-size:12px!important;
}
.seq-copy b{
    font-size:14px!important;
}
.seq-copy span{
    font-size:11px!important;
    line-height:1.55!important;
}
.seq-state{
    font-size:10px!important;
    padding:8px!important;
}
.coming{
    padding:23px!important;
}
.coming-badge{
    font-size:10px!important;
}
.coming h3{
    font-size:18px!important;
}
.coming p,
.coming div{
    font-size:11px!important;
    line-height:1.7!important;
}

/* Analytics */
.pipeline-card{
    padding:18px!important;
}
.pipeline-card b{
    font-size:27px!important;
}
.pipeline-card span{
    font-size:12px!important;
}
.chart-head b{font-size:14px!important}
.chart-head span{font-size:11px!important}

/* Captions */
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p{
    font-size:11px!important;
    line-height:1.5!important;
}

@media(max-width:1100px){
    .page-title{font-size:30px!important}
    section[data-testid="stSidebar"] .stButton>button{font-size:13px!important}
}


/* APOLLO-DEPTH REACH HOME */
.home-title{font-size:34px;font-weight:800;letter-spacing:-1.4px;margin-top:6px}
.home-sub{font-size:13px;color:#8b9a91;margin-top:4px}
.kpi6{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin:24px 0 14px}
.kpi{min-height:105px;padding:17px;border:1px solid rgba(255,255,255,.08);border-radius:10px;background:linear-gradient(145deg,#07150e,#041009)}
.kpi b{display:block;font-size:26px;line-height:1.1}
.kpi span{display:block;font-size:11px;color:#8b9990;margin-top:8px}
.home-grid{display:grid;grid-template-columns:1.15fr .9fr .7fr;gap:11px}
.home-card{border:1px solid rgba(255,255,255,.08);border-radius:10px;background:#06120c;padding:17px}
.home-card h3{font-size:16px;margin:0 0 12px}
.home-card-head{display:flex;align-items:center;justify-content:space-between}
.home-card-head a{font-size:10px;color:#42ef94}
.activity-item,.task-item,.quick-item{display:grid;grid-template-columns:36px 1fr auto;gap:10px;align-items:center;padding:12px 0;border-top:1px solid rgba(255,255,255,.05)}
.activity-item:first-of-type,.task-item:first-of-type{border-top:0}
.act-icon{width:34px;height:34px;border-radius:8px;display:grid;place-items:center;background:rgba(45,245,138,.08);color:#41ef93}
.activity-item b,.task-item b{
    display:block;
    font-size:12px;
    line-height:1.35;
    margin-bottom:5px;
}
.activity-item span,.task-item span{
    display:block;
    font-size:10px;
    line-height:1.5;
    color:#7c8b82;
}
.activity-item em,.task-item em{font-size:9px;color:#829087;font-style:normal}
.mini-tabs{display:flex;gap:8px;margin-bottom:8px}
.mini-tab{font-size:10px;color:#839087;padding:7px 11px;border-radius:99px}
.mini-tab.on{color:#42ef94;background:rgba(45,245,138,.09);border:1px solid rgba(45,245,138,.18)}
.home-chart{height:155px;display:flex;align-items:flex-end;gap:13px;padding:15px 4px 8px;border-bottom:1px solid rgba(255,255,255,.06)}
.home-chart i{display:block;flex:1;background:linear-gradient(#48f09a,#0d6d3c);border-radius:4px 4px 0 0}
.pipe-line{display:flex;justify-content:space-between;padding:9px 0;border-top:1px solid rgba(255,255,255,.05);font-size:11px}
.pipe-line span:first-child{color:#98a59e}.pipe-line b{color:#eaf3ee}
.recommend-table{margin-top:11px;border-top:1px solid rgba(255,255,255,.06)}
.rec-row{display:grid;grid-template-columns:1.35fr 1fr .65fr .8fr .55fr .9fr;gap:8px;align-items:center;padding:11px 0;border-bottom:1px solid rgba(255,255,255,.05);font-size:10px;color:#8d9a92}
.rec-row.head{font-size:9px;color:#56665c;text-transform:uppercase}
.rec-row strong{color:#eef6f1;font-size:11px}.fit{display:inline-block;background:rgba(45,245,138,.13);color:#42ef94;border-radius:6px;padding:5px 7px;font-weight:800}
.quick-item{grid-template-columns:30px 1fr auto}.quick-item b{font-size:11px}.quick-item span{color:#43ef95}
.ai-home{background:radial-gradient(circle at 100% 0%,rgba(45,245,138,.13),transparent 50%),#07170f}
@media(max-width:1200px){.kpi6{grid-template-columns:repeat(3,1fr)}.home-grid{grid-template-columns:1fr 1fr}.home-grid>.home-card:last-child{grid-column:1/-1}}


/* ============================================================
   DEEP WORKSPACE COMPONENTS
   ============================================================ */
.workspace-tabs{display:flex;gap:7px;margin:18px 0 12px;flex-wrap:wrap}
.workspace-tab{font-size:11px;padding:8px 12px;border:1px solid rgba(255,255,255,.08);border-radius:7px;color:#8b9990;background:#06120c}
.workspace-tab.on{color:#2df58a;border-color:rgba(45,245,138,.25);background:rgba(45,245,138,.08)}
.filter-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin:12px 0}
.filter-box{padding:13px;border:1px solid rgba(255,255,255,.07);border-radius:8px;background:#06120c}
.filter-box b{font-size:11px;display:block}.filter-box span{font-size:10px;color:#7e8c84;display:block;margin-top:5px}
.coverage-grid{display:grid;grid-template-columns:1.2fr .8fr;gap:12px;margin-top:14px}
.coverage-ring{width:150px;height:150px;border-radius:50%;margin:18px auto;display:grid;place-items:center;background:conic-gradient(#2df58a 0 38%,#10261a 38%);position:relative}
.coverage-ring:after{content:"";position:absolute;inset:13px;border-radius:50%;background:#06120c}
.coverage-ring div{position:relative;z-index:2;text-align:center}.coverage-ring b{display:block;font-size:30px}.coverage-ring span{font-size:10px;color:#829087}
.segment-row{display:grid;grid-template-columns:1.4fr .55fr 1fr .45fr;gap:10px;align-items:center;padding:12px 0;border-top:1px solid rgba(255,255,255,.05);font-size:11px}
.segment-row.head{font-size:9px;color:#59685f;text-transform:uppercase}.seg-track{height:7px;background:#11261a;border-radius:99px;overflow:hidden}.seg-track i{display:block;height:100%;background:#2df58a}
.memory-card{padding:15px;border:1px solid rgba(255,255,255,.07);border-radius:9px;background:#06120c}
.memory-card b{font-size:13px}.memory-card p{font-size:11px!important;color:#819087!important;line-height:1.55!important}
.kanban{display:grid;grid-template-columns:repeat(5,minmax(190px,1fr));gap:10px;overflow-x:auto;padding-bottom:8px}
.kanban-col{background:#05110b;border:1px solid rgba(255,255,255,.07);border-radius:9px;padding:11px;min-height:350px}
.kanban-head{display:flex;justify-content:space-between;font-size:11px;font-weight:800;margin-bottom:10px}.kanban-head span{color:#718078}
.deal-card{padding:12px;border:1px solid rgba(255,255,255,.07);border-radius:8px;background:#07170f;margin-bottom:8px}.deal-card b{font-size:11px}.deal-card p{font-size:9px!important;color:#78877e!important;margin:5px 0!important}
.integration-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:14px}.integration{padding:16px;border:1px solid rgba(255,255,255,.07);border-radius:9px;background:#06120c}.integration b{font-size:13px}.integration p{font-size:10px!important;color:#7e8d84!important;min-height:35px}.connect-pill{display:inline-block;margin-top:8px;padding:6px 9px;border:1px solid rgba(45,245,138,.2);border-radius:6px;color:#2df58a;font-size:9px}
.health-row{display:grid;grid-template-columns:1.3fr .55fr .65fr .65fr;gap:8px;padding:12px 0;border-top:1px solid rgba(255,255,255,.05);font-size:11px}.health-row.head{font-size:9px;color:#59685f;text-transform:uppercase}
.signal-row{display:grid;grid-template-columns:42px 1fr .7fr .5fr;gap:10px;align-items:center;padding:13px 0;border-top:1px solid rgba(255,255,255,.05)}.signal-row b{font-size:11px}.signal-row span{font-size:10px;color:#7c8b82}
.timeline{position:relative;margin:10px 0 0 14px;padding-left:22px;border-left:1px solid rgba(45,245,138,.18)}.timeline-item{position:relative;padding:0 0 20px}.timeline-item:before{content:"";position:absolute;left:-27px;top:4px;width:9px;height:9px;border-radius:50%;background:#2df58a;box-shadow:0 0 12px rgba(45,245,138,.3)}.timeline-item b{font-size:11px}.timeline-item p{font-size:10px!important;color:#7d8b82!important;margin:4px 0!important}
@media(max-width:1100px){.filter-grid{grid-template-columns:1fr 1fr}.coverage-grid{grid-template-columns:1fr}.integration-grid{grid-template-columns:1fr 1fr}}


/* APOLLO-DEPTH PROSPECTING + RECORDS */
.adv-search{display:grid;grid-template-columns:245px minmax(0,1fr);border:1px solid rgba(255,255,255,.07);border-radius:10px;overflow:hidden;margin-top:12px;min-height:570px}
.adv-filter{background:#06120c;border-right:1px solid rgba(255,255,255,.06);padding:11px}
.filter-search{padding:10px;border:1px solid rgba(255,255,255,.07);border-radius:7px;color:#718078;font-size:10px;margin-bottom:8px}
.filter-group{padding:11px 7px;border-top:1px solid rgba(255,255,255,.045);font-size:11px;color:#a1ada6;display:flex;justify-content:space-between}.filter-group.ai{color:#2df58a}
.adv-results{background:#04100a;padding:12px;overflow:auto}.bulkbar{display:flex;gap:7px;align-items:center;flex-wrap:wrap;margin-bottom:10px}.bulk{padding:7px 9px;border:1px solid rgba(255,255,255,.08);border-radius:6px;font-size:9px;color:#8d9a92}.bulk.green{color:#2df58a;border-color:rgba(45,245,138,.2)}
.profile-grid{display:grid;grid-template-columns:minmax(0,1.35fr) .65fr;gap:11px;margin-top:12px}.profile-card{padding:18px;border:1px solid rgba(255,255,255,.07);border-radius:10px;background:#06120c}.profile-tabs{display:flex;gap:6px;flex-wrap:wrap;margin:12px 0}.profile-tab{padding:7px 10px;border-radius:6px;font-size:10px;color:#829087}.profile-tab.on{background:rgba(45,245,138,.09);color:#2df58a}
.workflow-canvas{display:grid;grid-template-columns:230px 1fr;gap:12px;margin-top:12px}.workflow-tools{padding:14px;background:#06120c;border:1px solid rgba(255,255,255,.07);border-radius:9px}.workflow-tool{padding:10px;border:1px solid rgba(255,255,255,.06);border-radius:7px;margin-top:7px;font-size:10px}.workflow-stage{padding:20px;min-height:470px;border:1px solid rgba(255,255,255,.07);border-radius:9px;background:radial-gradient(circle at 50% 10%,rgba(45,245,138,.05),transparent 30%),#04100a}.flow-node{width:min(420px,90%);margin:0 auto 13px;padding:14px;border:1px solid rgba(45,245,138,.17);border-radius:9px;background:#07170f}.flow-node b{font-size:11px}.flow-node span{font-size:9px;color:#7f8e85;display:block;margin-top:4px}.flow-arrow{text-align:center;color:#2df58a;margin:-4px 0 8px}
.saved-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px}.saved-card{padding:16px;border:1px solid rgba(255,255,255,.07);border-radius:9px;background:#06120c}.saved-card b{font-size:13px}.saved-card p{font-size:10px!important;color:#7f8e85!important;line-height:1.55!important}.alert{display:inline-block;font-size:9px;color:#2df58a;background:rgba(45,245,138,.08);border-radius:99px;padding:5px 7px}
@media(max-width:1050px){.adv-search,.workflow-canvas,.profile-grid{grid-template-columns:1fr}.adv-filter{display:none}.saved-grid{grid-template-columns:1fr 1fr}}


/* Keep the full REACH navigation visible throughout the internal app.
   The Landing page does not call sidebar(), so it remains clean. */
[data-testid="stSidebar"]{
    display:flex !important;
    visibility:visible !important;
    opacity:1 !important;
}
[data-testid="stSidebar"][aria-expanded="true"]{
    min-width:250px !important;
    width:250px !important;
}


/* ============================================================
   FORCE REACH SIDEBAR VISIBLE ON DESKTOP
   Fixes Streamlit remembering/collapsing the sidebar.
   ============================================================ */
@media (min-width: 901px) {
  section[data-testid="stSidebar"] {
      display: block !important;
      visibility: visible !important;
      opacity: 1 !important;
      position: fixed !important;
      top: 0 !important;
      left: 0 !important;
      bottom: 0 !important;
      width: 250px !important;
      min-width: 250px !important;
      max-width: 250px !important;
      height: 100vh !important;
      transform: translateX(0) !important;
      margin-left: 0 !important;
      z-index: 999999 !important;
      overflow: visible !important;
      background: #030b07 !important;
  }

  section[data-testid="stSidebar"] > div {
      display: block !important;
      visibility: visible !important;
      opacity: 1 !important;
      width: 250px !important;
      min-width: 250px !important;
      height: 100vh !important;
      overflow-y: auto !important;
      overflow-x: hidden !important;
      transform: none !important;
  }

  section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
      display: block !important;
      visibility: visible !important;
      opacity: 1 !important;
      width: 250px !important;
      min-width: 250px !important;
      transform: none !important;
  }

  /* Reserve permanent room for the sidebar so Companies never sits underneath it. */
  [data-testid="stAppViewContainer"] > .main {
      margin-left: 250px !important;
      width: calc(100% - 250px) !important;
  }

  [data-testid="stMain"] {
      margin-left: 250px !important;
      width: calc(100% - 250px) !important;
  }

  /* Do not let Streamlit's collapsed state slide the sidebar off-screen. */
  section[data-testid="stSidebar"][aria-expanded="false"],
  section[data-testid="stSidebar"][aria-expanded="true"] {
      transform: translateX(0) !important;
      left: 0 !important;
      display: block !important;
      visibility: visible !important;
  }
}


/* REACH top controls: keep them readable on the dark workspace */
div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
    background: rgba(4, 18, 12, .94);
    color: #dff7e9;
    border: 1px solid rgba(46, 234, 122, .16);
}
div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
    background: rgba(11, 42, 27, .98);
    color: #2EEA7A;
    border-color: rgba(46, 234, 122, .45);
}
div[data-testid="stHorizontalBlock"] button p {
    color: inherit !important;
    font-weight: 650;
}

/* Improve small supporting copy/readability throughout the internal app */
[data-testid="stAppViewContainer"] .stCaption,
[data-testid="stAppViewContainer"] small {
    font-size: 12px !important;
    line-height: 1.5 !important;
    color: #91a89b !important;
}
[data-testid="stAppViewContainer"] label p {
    font-size: 12px !important;
    color: #d4e6dc !important;
}
[data-testid="stAppViewContainer"] .stAlert p {
    font-size: 12px !important;
    line-height: 1.55 !important;
}
[data-testid="stAppViewContainer"] input,
[data-testid="stAppViewContainer"] textarea,
[data-testid="stAppViewContainer"] [data-baseweb="select"] {
    font-size: 13px !important;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# REACH RESPONSIVE HOTFIX — recruiter portfolio
# ============================================================
st.markdown(r"""
<style>
html,body,.stApp{overflow-x:hidden!important}
img,svg,video,canvas{max-width:100%!important;height:auto}
.table-shell,.people-results,.recommend-table,[data-testid="stDataFrame"]{max-width:100%!important;overflow-x:auto!important;-webkit-overflow-scrolling:touch}

@media(max-width:1180px){
.block-container{padding-left:1.2rem!important;padding-right:1.2rem!important}
.kpi6{grid-template-columns:repeat(3,minmax(0,1fr))!important}
.home-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}
.filter-grid,.metrics4,.pipeline{grid-template-columns:repeat(2,minmax(0,1fr))!important}
.coverage-grid,.outreach-layout{grid-template-columns:1fr!important}
}

@media(max-width:820px){
.block-container{width:100%!important;max-width:100%!important;padding:.8rem!important}
section[data-testid="stSidebar"]{min-width:min(86vw,290px)!important;max-width:min(86vw,290px)!important}
.landing-links,.nav-sign{display:none!important}
.landing-nav{height:56px!important;margin:0!important;gap:8px!important}
.brand{font-size:16px!important;white-space:nowrap!important}.nav-actions{margin-left:auto!important}
.landing-hero{width:100%!important;max-width:100%!important;min-width:0!important;min-height:auto!important;padding:36px 0 40px!important;margin:0 auto!important;overflow:hidden!important}
.landing-hero:before{width:100vw!important;max-width:100vw!important;top:-90px!important}
.landing-hero h1{width:100%!important;max-width:100%!important;padding:0 4px!important;font-size:clamp(36px,9.5vw,50px)!important;line-height:1.04!important;letter-spacing:-2px!important;text-wrap:balance!important;overflow-wrap:normal!important;word-break:normal!important}
.landing-hero p{width:100%!important;max-width:650px!important;padding:0 5px!important;font-size:13px!important;line-height:1.65!important}
.hero-actions{width:100%!important;max-width:390px!important;flex-direction:column!important;align-items:stretch!important;margin:20px auto 0!important}
.hero-primary,.hero-secondary{width:100%!important;min-height:44px!important;text-align:center!important;font-size:11px!important;padding:12px 14px!important}
.hero-demo{width:100%!important;max-width:100%!important;margin-top:28px!important}
.demo-grid{grid-template-columns:1fr!important;min-height:auto!important}.demo-side{display:none!important}.demo-content{min-width:0!important;padding:12px!important}
.demo-metrics{grid-template-columns:repeat(2,minmax(0,1fr))!important}.demo-table{overflow-x:auto!important}.demo-row{min-width:430px!important}
.market-entry-card,div[data-testid="stForm"]{width:100%!important;max-width:100%!important}
.market-entry-top{grid-template-columns:1fr!important;gap:18px!important}.market-entry-copy{padding-right:0!important;border-right:0!important}
.market-entry-benefits{grid-template-columns:1fr!important}.market-benefit:first-child{grid-row:auto!important}
.app-top{height:auto!important;grid-template-columns:1fr!important;gap:8px!important}.global-search{width:100%!important;min-width:0!important}.top-icons{justify-content:flex-start!important;flex-wrap:wrap!important}
.kpi6,.metrics4,.pipeline,.home-grid,.filter-grid,.ready-layout,.outreach-layout,.coverage-grid{grid-template-columns:1fr!important}
.home-grid>.home-card:last-child{grid-column:auto!important}
.toolbar,.status-tabs,.workspace-tabs,.mini-tabs{max-width:100%!important;overflow-x:auto!important;flex-wrap:nowrap!important;padding-bottom:5px!important;-webkit-overflow-scrolling:touch}
.toolbar>*,.status-tabs>*,.workspace-tabs>*,.mini-tabs>*{flex:0 0 auto!important}.tool.push{margin-left:0!important}
.people-layout{grid-template-columns:1fr!important;min-height:0!important}.filters{display:block!important;border-right:0!important;border-bottom:1px solid rgba(255,255,255,.06)!important}
.company-head,.company-row{min-width:700px!important}.people-head,.people-row{min-width:680px!important}.rec-row{min-width:720px!important}
.seq-line{grid-template-columns:52px 34px minmax(0,1fr)!important;gap:9px!important}.seq-state{grid-column:2/-1!important;text-align:left!important}
.chart{overflow-x:auto!important}.bars,.bar-labels{min-width:520px!important}
}

@media(max-width:600px){
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{width:100%!important;max-width:100%!important;overflow-x:hidden!important}
.block-container{width:100%!important;max-width:100%!important;padding:.65rem 14px 3rem!important;margin:0!important}
.landing-nav{width:100%!important;max-width:100%!important;height:54px!important;padding:0 2px!important;overflow:hidden!important}
.brand{font-size:15px!important;flex:0 0 auto!important}.nav-cta{font-size:9px!important;padding:8px 9px!important;white-space:nowrap!important}
.landing-hero{padding:30px 0 36px!important}
.eyebrow-pill{max-width:calc(100vw - 50px)!important;white-space:normal!important;font-size:8px!important;line-height:1.35!important}
.landing-hero h1{font-size:clamp(33px,10.2vw,42px)!important;line-height:1.04!important;letter-spacing:-1.6px!important;margin:16px auto 14px!important;padding:0 2px!important}
.landing-hero p{max-width:350px!important;font-size:12px!important;line-height:1.6!important;margin-left:auto!important;margin-right:auto!important}
.hero-actions{max-width:350px!important}
.market-entry-card{padding:17px 13px 12px!important}.market-entry-title{font-size:22px!important}div[data-testid="stForm"]{padding:7px 13px 15px!important}
.page-title,.home-title{font-size:27px!important;overflow-wrap:break-word!important}.page-sub,.home-sub{font-size:12px!important}
.kpi,.metricbox,.pipeline-card,.home-card,.surface,.overview-card,.score-card,.sequence,.coming{min-width:0!important;max-width:100%!important}
.activity-item,.task-item,.quick-item{grid-template-columns:32px minmax(0,1fr)!important;gap:9px!important}
.activity-item em,.task-item em{grid-column:2!important;justify-self:start!important}
.stButton>button,[data-testid="stFormSubmitButton"] button{min-height:44px!important;white-space:normal!important}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-baseweb="select"]>div{font-size:16px!important}
.closing h1{font-size:34px!important}.closing p{font-size:12px!important;line-height:1.6!important}.closing-globe{width:135px!important;height:135px!important}
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================

load_dotenv()


def get_supabase_client(require_auth=False):
    """Return this Streamlit session's Supabase client and restore its auth session when available."""
    if "supabase_client" not in st.session_state:
        url = os.getenv("SUPABASE_URL", "").strip()
        key = os.getenv("SUPABASE_ANON_KEY", "").strip()
        if not url or not key:
            raise RuntimeError("SUPABASE_URL or SUPABASE_ANON_KEY is missing from .env")
        st.session_state.supabase_client = create_client(url, key)

    client = st.session_state.supabase_client
    access_token = st.session_state.get("supabase_access_token")
    refresh_token = st.session_state.get("supabase_refresh_token")

    # Streamlit reruns the script frequently. Explicitly restore the authenticated
    # Supabase session so Postgres auth.uid() is present for every RLS-protected call.
    if access_token and refresh_token:
        try:
            current = client.auth.get_session()
            current_access = getattr(current, "access_token", None) if current else None
            if current_access != access_token:
                restored = client.auth.set_session(access_token, refresh_token)
                restored_session = getattr(restored, "session", None)
                if restored_session:
                    st.session_state.supabase_access_token = restored_session.access_token
                    st.session_state.supabase_refresh_token = restored_session.refresh_token
        except Exception:
            restored = client.auth.set_session(access_token, refresh_token)
            restored_session = getattr(restored, "session", None)
            if restored_session:
                st.session_state.supabase_access_token = restored_session.access_token
                st.session_state.supabase_refresh_token = restored_session.refresh_token

    if require_auth:
        try:
            verified = client.auth.get_user()
            verified_user = getattr(verified, "user", None)
        except Exception as exc:
            raise RuntimeError("Your REACH login session is no longer authenticated. Please sign out and sign in again.") from exc
        if not verified_user:
            raise RuntimeError("Your REACH login session is no longer authenticated. Please sign out and sign in again.")
        st.session_state.auth_user = verified_user
        st.session_state.auth_email = verified_user.email or st.session_state.get("auth_email", "")

    return client


def load_reach_workspace():
    """Load an existing workspace first; create one only when the user truly has none."""
    user = st.session_state.get("auth_user")
    if not user:
        return None

    supabase = get_supabase_client(require_auth=True)
    user = st.session_state.get("auth_user")
    user_id = str(user.id)

    # 1) First try the user's workspace membership. Keep this query simple instead
    # of relying on a nested PostgREST relationship during authentication.
    membership_response = (
        supabase.table("workspace_members")
        .select("workspace_id, role")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    memberships = membership_response.data or []

    workspace_id = None
    workspace_name = None

    if memberships:
        workspace_id = memberships[0].get("workspace_id")

    # 2) If RLS/relationship loading did not return the membership, use the
    # actual owner_id column from the REACH workspaces schema. This also prevents
    # another workspace being created for an owner who already has one.
    if not workspace_id:
        owner_response = (
            supabase.table("workspaces")
            .select("id, name")
            .eq("owner_id", user_id)
            .order("created_at", desc=False)
            .limit(1)
            .execute()
        )
        owned = owner_response.data or []
        if owned:
            workspace_id = owned[0].get("id")
            workspace_name = owned[0].get("name")

    # 3) Only a genuinely new user reaches this point. Migration 12 securely
    # creates the workspace and owner membership using auth.uid().
    if not workspace_id:
        default_name = f"{(user.email or 'REACH').split('@')[0].title()}'s Workspace"
        created = supabase.rpc(
            "create_reach_workspace",
            {"p_name": default_name},
        ).execute()
        workspace_id = created.data
        if not workspace_id:
            raise RuntimeError("REACH could not create your workspace.")
        workspace_name = default_name

    # 4) Fetch the display name separately. If this read is restricted for any
    # reason, authentication still succeeds and REACH uses a safe display name.
    if workspace_id and not workspace_name:
        try:
            workspace_response = (
                supabase.table("workspaces")
                .select("id, name")
                .eq("id", workspace_id)
                .limit(1)
                .execute()
            )
            rows = workspace_response.data or []
            if rows:
                workspace_name = rows[0].get("name")
        except Exception:
            workspace_name = None

    st.session_state.workspace_id = str(workspace_id)
    st.session_state.workspace_name = workspace_name or "REACH Workspace"
    return st.session_state.workspace_id


def complete_sign_in(auth_response):
    user = getattr(auth_response, "user", None)
    session = getattr(auth_response, "session", None)
    if not user or not session:
        return False
    st.session_state.auth_user = user
    st.session_state.auth_email = user.email or ""
    st.session_state.supabase_access_token = session.access_token
    st.session_state.supabase_refresh_token = session.refresh_token
    # Confirm the same client is carrying the authenticated session before any RLS-protected query.
    get_supabase_client(require_auth=True)
    load_reach_workspace()
    try:
        load_saved_market_context()
    except Exception:
        # Saved market data should never prevent a valid user from signing in.
        pass
    try:
        load_saved_companies()
    except Exception:
        # A company-load problem should not prevent a valid user from signing in.
        pass

    # A completed authentication always enters the private REACH workspace.
    # Do not leave an authenticated user on the public Landing page.
    destination = st.session_state.get("post_auth_page") or "Home"
    if destination in ("Landing", "Auth"):
        destination = "Home"
    st.session_state.page = destination
    st.session_state.post_auth_page = "Home"
    return True


def _normalise_company_for_reach(row):
    """Convert a Supabase company row back into the shape the REACH UI expects."""
    if not isinstance(row, dict):
        return {}
    return {
        **row,
        "name": row.get("name") or row.get("company_name") or "Unknown organisation",
        "company_number": row.get("company_number") or "",
        "status": row.get("status") or "discovered",
        "company_type": row.get("company_type") or "",
        "address": row.get("registered_address") or row.get("address") or row.get("location") or "",
        "relevance_score": row.get("relevance_score"),
        "source": row.get("source") or "Companies House",
    }


def load_saved_companies():
    """Load companies linked to the active saved strategy when possible."""
    workspace_id = st.session_state.get("workspace_id")
    if not workspace_id:
        return []

    supabase = get_supabase_client(require_auth=True)
    strategy_id = st.session_state.get("strategy_id")
    rows = []

    if strategy_id:
        links = (
            supabase.table("company_market_memberships").select("company_id")
            .eq("workspace_id", workspace_id)
            .eq("strategy_id", strategy_id)
            .execute().data or []
        )
        company_ids = list(dict.fromkeys(
            str(row.get("company_id")) for row in links if row.get("company_id")
        ))

        if company_ids:
            rows = (
                supabase.table("companies").select("*")
                .eq("workspace_id", workspace_id)
                .in_("id", company_ids)
                .order("created_at", desc=True)
                .execute().data or []
            )

    if not rows:
        rows = (
            supabase.table("companies").select("*")
            .eq("workspace_id", workspace_id)
            .order("created_at", desc=True)
            .execute().data or []
        )

    companies = [_normalise_company_for_reach(row) for row in rows]
    st.session_state.market_results = companies
    st.session_state.market_built = bool(companies)
    return companies


def _first_list(data, *keys):
    for key in keys:
        value = (data or {}).get(key)
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
    return []


def _first_text(data, *keys, default=""):
    for key in keys:
        value = (data or {}).get(key)
        if value not in (None, "", []):
            return str(value).strip()
    return default


def save_product_and_strategy(analysis):
    """Persist the user's product and current AI market strategy using the exact REACH schema."""
    workspace_id = st.session_state.get("workspace_id")
    user = st.session_state.get("auth_user")
    if not workspace_id or not user:
        raise RuntimeError("A signed-in REACH workspace is required before saving a strategy.")

    supabase = get_supabase_client(require_auth=True)
    description = (st.session_state.get("product_description") or "").strip()
    if not description:
        raise RuntimeError("Product or service description is empty.")

    product_name = _first_text(analysis, "product_name", "name", default="Your product or service")
    product_type = _first_text(analysis, "product_type", "type", default="service")

    # Reuse the same product for the same workspace + description instead of creating duplicates.
    existing_product = (
        supabase.table("products")
        .select("id")
        .eq("workspace_id", workspace_id)
        .eq("description", description)
        .limit(1)
        .execute().data or []
    )
    product_payload = {
        "workspace_id": workspace_id,
        "created_by": str(user.id),
        "name": product_name,
        "description": description,
        "product_type": product_type,
    }
    if existing_product:
        product_id = existing_product[0]["id"]
        supabase.table("products").update(product_payload).eq("id", product_id).execute()
    else:
        created = supabase.table("products").insert(product_payload).execute().data or []
        if not created:
            raise RuntimeError("REACH could not save the product.")
        product_id = created[0]["id"]

    summary = _first_text(analysis, "summary", "market_summary", "problem_solved", default=description)
    target_description = _first_text(
        analysis, "target_market_description", "target_market", "ideal_customer_profile",
        default="; ".join(_first_list(analysis, "customer_segments", "target_segments", "potential_customers", "segments"))
    )
    location = (st.session_state.get("selected_location") or "United Kingdom").strip()
    strategy_name = f"{product_name} market strategy"

    existing_strategy = (
        supabase.table("market_strategies")
        .select("id")
        .eq("workspace_id", workspace_id)
        .eq("product_id", product_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute().data or []
    )
    strategy_payload = {
        "workspace_id": workspace_id,
        "product_id": product_id,
        "strategy_name": strategy_name,
        "summary": summary,
        "target_market_description": target_description or None,
        "geographic_scope": location,
        "strategy_version": 1,
        "status": "active",
        "ai_model": "gpt-4o-mini",
        "metadata": {"website": st.session_state.get("website") or "", "analysis": analysis or {}},
    }
    if existing_strategy:
        strategy_id = existing_strategy[0]["id"]
        supabase.table("market_strategies").update(strategy_payload).eq("id", strategy_id).execute()
        # Child records represent the current strategy. Rebuild them to avoid duplicates after re-analysis.
        supabase.table("market_segments").delete().eq("strategy_id", strategy_id).execute()
        supabase.table("personas").delete().eq("strategy_id", strategy_id).execute()
        supabase.table("market_search_terms").delete().eq("strategy_id", strategy_id).execute()
    else:
        created = supabase.table("market_strategies").insert(strategy_payload).execute().data or []
        if not created:
            raise RuntimeError("REACH could not save the market strategy.")
        strategy_id = created[0]["id"]

    segments = _first_list(analysis, "customer_segments", "target_segments", "potential_customers", "segments")
    for priority, segment in enumerate(segments, start=1):
        supabase.table("market_segments").insert({
            "workspace_id": workspace_id,
            "strategy_id": strategy_id,
            "name": segment,
            "description": None,
            "priority": priority,
            "status": "active",
            "metadata": {},
        }).execute()

    roles = _first_list(analysis, "decision_makers", "decision_maker_roles", "decision_maker_titles", "people_to_reach", "roles")
    if roles:
        supabase.table("personas").insert({
            "workspace_id": workspace_id,
            "strategy_id": strategy_id,
            "name": "Primary decision-makers",
            "description": "Decision-maker roles identified by REACH for this market strategy.",
            "job_titles": roles,
            "seniorities": [],
            "departments": [],
            "pain_points": _first_list(analysis, "pain_points"),
            "goals": [],
            "priority": 1,
        }).execute()

    terms = _first_list(analysis, "search_terms", "discovery_searches", "discovery_terms", "organisation_search_terms", "organization_search_terms")
    for priority, term in enumerate(terms, start=1):
        supabase.table("market_search_terms").insert({
            "workspace_id": workspace_id,
            "strategy_id": strategy_id,
            "search_term": term,
            "source": "REACH AI",
            "priority": priority,
            "active": True,
        }).execute()

    st.session_state.product_id = str(product_id)
    st.session_state.strategy_id = str(strategy_id)
    return str(product_id), str(strategy_id)


def load_saved_market_context():
    """Restore the saved strategy that actually contains the user's built market."""
    workspace_id = st.session_state.get("workspace_id")
    if not workspace_id:
        return False

    supabase = get_supabase_client(require_auth=True)

    products = (
        supabase.table("products").select("*")
        .eq("workspace_id", workspace_id).execute().data or []
    )
    strategies = (
        supabase.table("market_strategies").select("*")
        .eq("workspace_id", workspace_id)
        .order("created_at", desc=True).execute().data or []
    )
    if not products or not strategies:
        return False

    products_by_id = {str(row.get("id")): row for row in products if row.get("id")}

    all_segments = (
        supabase.table("market_segments").select("strategy_id,name,priority")
        .eq("workspace_id", workspace_id).execute().data or []
    )
    all_personas = (
        supabase.table("personas").select("strategy_id,job_titles,pain_points,priority")
        .eq("workspace_id", workspace_id).execute().data or []
    )
    all_terms = (
        supabase.table("market_search_terms").select("strategy_id,search_term,priority,active")
        .eq("workspace_id", workspace_id).execute().data or []
    )
    all_memberships = (
        supabase.table("company_market_memberships").select("strategy_id,company_id")
        .eq("workspace_id", workspace_id).execute().data or []
    )

    def sid(row):
        value = row.get("strategy_id")
        return str(value) if value else ""

    def priority(row):
        value = row.get("priority")
        return value if isinstance(value, (int, float)) else 999999

    def score(strategy):
        strategy_id = str(strategy.get("id"))
        memberships = sum(1 for row in all_memberships if sid(row) == strategy_id)
        terms = sum(1 for row in all_terms if sid(row) == strategy_id and row.get("search_term") and row.get("active", True))
        segments = sum(1 for row in all_segments if sid(row) == strategy_id and row.get("name"))
        personas = sum(1 for row in all_personas if sid(row) == strategy_id and (row.get("job_titles") or []))
        return memberships, terms, segments, personas

    strategy = max(strategies, key=score)
    strategy_id = strategy.get("id")
    if not strategy_id:
        return False
    strategy_id_text = str(strategy_id)

    product_id = strategy.get("product_id")
    product = products_by_id.get(str(product_id))
    if not product:
        product = max(products, key=lambda row: str(row.get("created_at") or ""))
        product_id = product.get("id")

    segments = sorted(
        [row for row in all_segments if sid(row) == strategy_id_text and row.get("name")],
        key=priority,
    )
    personas = sorted(
        [row for row in all_personas if sid(row) == strategy_id_text],
        key=priority,
    )
    terms = sorted(
        [row for row in all_terms if sid(row) == strategy_id_text and row.get("search_term") and row.get("active", True)],
        key=priority,
    )

    metadata = strategy.get("metadata") or {}
    stored_analysis = metadata.get("analysis") if isinstance(metadata, dict) else None
    analysis = dict(stored_analysis) if isinstance(stored_analysis, dict) else {}

    analysis["product_name"] = analysis.get("product_name") or product.get("name") or "Your product or service"
    analysis["customer_segments"] = list(dict.fromkeys(
        str(row["name"]).strip() for row in segments if str(row.get("name") or "").strip()
    ))

    roles = []
    pain_points = []
    for persona in personas:
        roles.extend(persona.get("job_titles") or [])
        pain_points.extend(persona.get("pain_points") or [])

    analysis["decision_makers"] = list(dict.fromkeys(
        str(value).strip() for value in roles if str(value).strip()
    ))
    if pain_points:
        analysis["pain_points"] = list(dict.fromkeys(
            str(value).strip() for value in pain_points if str(value).strip()
        ))

    analysis["search_terms"] = list(dict.fromkeys(
        str(row["search_term"]).strip() for row in terms if str(row.get("search_term") or "").strip()
    ))

    if not (analysis["customer_segments"] or analysis["decision_makers"] or analysis["search_terms"]):
        return False

    st.session_state.product_id = str(product_id) if product_id else None
    st.session_state.strategy_id = strategy_id_text
    st.session_state.product_description = product.get("description") or ""
    st.session_state.selected_location = strategy.get("geographic_scope") or "United Kingdom"
    st.session_state.website = metadata.get("website", "") if isinstance(metadata, dict) else ""
    st.session_state.analysis = analysis
    return True


def save_discovered_companies(companies):
    """Persist Companies House discoveries and link them to the active market strategy."""
    workspace_id = st.session_state.get("workspace_id")
    strategy_id = st.session_state.get("strategy_id")
    if not workspace_id:
        raise RuntimeError("No REACH workspace is loaded.")
    if not strategy_id:
        analysis = st.session_state.get("analysis") or {}
        _, strategy_id = save_product_and_strategy(analysis)

    supabase = get_supabase_client(require_auth=True)
    saved = 0
    for company in companies or []:
        name = company_name(company)
        number = str(company.get("company_number") or "").strip()
        # REACH workflow status is separate from the Companies House company status.
        # A newly discovered organisation always enters REACH as `discovered`.
        source_company_status = str(company.get("company_status") or company.get("status") or "").strip() or None
        status = "discovered"
        company_type = str(company.get("company_type") or "").strip() or None
        score = company.get("relevance_score")
        source_id = number or str(company.get("source_id") or "").strip() or None
        address = company.get("registered_office_address") or company.get("address") or {}
        if not isinstance(address, dict):
            address = {}

        existing = []
        if number:
            existing = (supabase.table("companies").select("id").eq("workspace_id", workspace_id)
                        .eq("company_number", number).limit(1).execute().data or [])
        if not existing and name:
            existing = (supabase.table("companies").select("id").eq("workspace_id", workspace_id)
                        .eq("name", name).limit(1).execute().data or [])

        payload = {
            "workspace_id": workspace_id,
            "name": name,
            "legal_name": company.get("legal_name") or name,
            "company_number": number or None,
            "company_type": company_type,
            "status": status,
            "description": company.get("description"),
            "industry": company.get("industry"),
            "primary_domain": company.get("primary_domain") or company.get("domain"),
            "website_url": company.get("website_url") or company.get("website"),
            "phone": company.get("phone"),
            "country": address.get("country") or company.get("country"),
            "region": address.get("region") or address.get("county") or company.get("region"),
            "city": address.get("locality") or address.get("city") or company.get("city"),
            "postcode": address.get("postal_code") or address.get("postcode") or company.get("postcode"),
            "source": "Companies House",
            "source_id": source_id,
            "relevance_score": score if isinstance(score, (int, float)) else None,
            "verified": bool(company.get("verified", False)),
            "metadata": {"companies_house": company, "companies_house_status": source_company_status},
        }
        if existing:
            company_id = existing[0]["id"]
            supabase.table("companies").update(payload).eq("id", company_id).execute()
        else:
            created = supabase.table("companies").insert(payload).execute().data or []
            if not created:
                continue
            company_id = created[0]["id"]

        membership = (supabase.table("company_market_memberships").select("id")
                      .eq("workspace_id", workspace_id).eq("company_id", company_id)
                      .eq("strategy_id", strategy_id).limit(1).execute().data or [])
        membership_payload = {
            "workspace_id": workspace_id,
            "company_id": company_id,
            "strategy_id": strategy_id,
            "relevance_score": score if isinstance(score, (int, float)) else None,
            "fit_score": company.get("fit_score") if isinstance(company.get("fit_score"), (int, float)) else None,
            "qualification_status": "unreviewed",
            "discovery_source": "Companies House",
            "discovery_query": company.get("discovery_query") or company.get("search_term"),
        }
        if membership:
            supabase.table("company_market_memberships").update(membership_payload).eq("id", membership[0]["id"]).execute()
        else:
            supabase.table("company_market_memberships").insert(membership_payload).execute()
        saved += 1

    load_saved_companies()
    return saved



def ensure_saved_company_memberships():
    """Link already-saved workspace companies to the active strategy in one small batch.

    This is deliberately idempotent: existing links are left alone, and only
    missing links are inserted. It lets REACH recover cleanly if Streamlit lost
    its browser connection after company rows were saved but before every
    company-market link finished.
    """
    workspace_id = st.session_state.get("workspace_id")
    strategy_id = st.session_state.get("strategy_id")
    if not workspace_id or not strategy_id:
        return 0

    supabase = get_supabase_client(require_auth=True)
    companies = (
        supabase.table("companies")
        .select("id,relevance_score")
        .eq("workspace_id", workspace_id)
        .execute().data or []
    )
    if not companies:
        return 0

    existing_links = (
        supabase.table("company_market_memberships")
        .select("company_id")
        .eq("workspace_id", workspace_id)
        .eq("strategy_id", strategy_id)
        .execute().data or []
    )
    linked_ids = {str(row.get("company_id")) for row in existing_links if row.get("company_id")}

    missing = []
    for company in companies:
        company_id = company.get("id")
        if not company_id or str(company_id) in linked_ids:
            continue
        score = company.get("relevance_score")
        missing.append({
            "workspace_id": workspace_id,
            "company_id": company_id,
            "strategy_id": strategy_id,
            "relevance_score": score if isinstance(score, (int, float)) else None,
            "qualification_status": "unreviewed",
            "discovery_source": "Companies House",
        })

    restored = 0
    for row in missing:
        try:
            # Insert one relationship at a time so a duplicate created by an
            # earlier/parallel rerun cannot make the whole recovery fail.
            supabase.table("company_market_memberships").insert(row).execute()
            restored += 1
        except Exception as exc:
            message = str(exc).lower()
            # PostgreSQL 23505 = unique violation. For this recovery routine it
            # simply means the company/strategy link already exists, which is
            # the desired end state, so continue safely.
            if "23505" in message or "duplicate key value violates unique constraint" in message:
                continue
            raise
    return restored

def sign_out_reach():
    try:
        get_supabase_client().auth.sign_out()
    except Exception:
        pass
    st.session_state.supabase_access_token = None
    st.session_state.supabase_refresh_token = None
    for key in ("auth_user", "auth_email", "workspace_id", "workspace_name", "product_id", "strategy_id", "supabase_client"):
        st.session_state.pop(key, None)
    st.session_state.auth_user = None
    st.session_state.auth_email = ""
    st.session_state.workspace_id = None
    st.session_state.workspace_name = ""
    st.session_state.market_results = []
    st.session_state.market_built = False
    st.session_state.analysis = None
    st.session_state.product_description = ""
    st.session_state.page = "Landing"
    st.rerun()


def require_auth(destination="Home"):
    if st.session_state.get("auth_user"):
        return True
    st.session_state.post_auth_page = destination
    st.session_state.page = "Auth"
    st.rerun()


def render_auth_page():
    st.markdown("""
    <style>
    section[data-testid="stSidebar"]{display:none!important}
    [data-testid="stMain"]{margin-left:0!important;width:100%!important}
    .auth-wrap{max-width:520px;margin:6vh auto 0;text-align:center}
    .auth-logo{font-size:30px;font-weight:900;letter-spacing:-1px}.auth-logo b{color:#2df58a}
    .auth-title{font-size:38px;font-weight:850;letter-spacing:-1.5px;margin-top:28px}
    .auth-sub{color:#8fa097;font-size:13px;line-height:1.6;margin:8px 0 24px}
    .auth-card{max-width:480px;margin:0 auto;padding:24px;border:1px solid rgba(45,245,138,.16);border-radius:14px;background:#06120c}
    </style>
    <div class="auth-wrap">
      <div class="auth-logo">REACH<b>.</b></div>
      <div class="auth-title">Your market. One workspace.</div>
      <div class="auth-sub">Sign in to keep your market research, companies, people, outreach and opportunities connected to your REACH workspace.</div>
    </div>
    """, unsafe_allow_html=True)

    left, centre, right = st.columns([1.25, 1, 1.25])
    with centre:
        mode = st.segmented_control(
            "Account", ["Sign in", "Create account"],
            default=st.session_state.get("auth_mode", "Sign in"),
            label_visibility="collapsed",
            key="auth_segment"
        )
        st.session_state.auth_mode = mode or "Sign in"

        if st.session_state.auth_mode == "Create account":
            display_name = st.text_input("Name", placeholder="Your name", key="signup_name")
        else:
            display_name = ""

        email = st.text_input("Email", placeholder="you@company.com", key="auth_email_input")
        password = st.text_input("Password", type="password", placeholder="At least 6 characters", key="auth_password_input")

        action_label = "Create my REACH account →" if st.session_state.auth_mode == "Create account" else "Sign in to REACH →"
        if st.button(action_label, type="primary", use_container_width=True, key="auth_submit"):
            if not email.strip() or not password:
                st.warning("Enter your email and password.")
            elif len(password) < 6:
                st.warning("Your password must be at least 6 characters.")
            else:
                try:
                    supabase = get_supabase_client()
                    if st.session_state.auth_mode == "Create account":
                        response = supabase.auth.sign_up({
                            "email": email.strip(),
                            "password": password,
                            "options": {"data": {"display_name": display_name.strip()}}
                        })
                        if complete_sign_in(response):
                            st.rerun()
                        else:
                            st.success("Account created. Check your email to confirm your address, then return here and sign in.")
                            st.session_state.auth_mode = "Sign in"
                    else:
                        response = supabase.auth.sign_in_with_password({"email": email.strip(), "password": password})
                        if complete_sign_in(response):
                            st.rerun()
                        else:
                            st.error("REACH could not sign you in.")
                except Exception as exc:
                    st.error("REACH could not complete that account action.")
                    st.caption(str(exc))

        if st.button("← Back to REACH", use_container_width=True, key="auth_back"):
            st.session_state.page = "Landing"
            st.rerun()

def nav_to(page):
    st.session_state.page = page
    st.rerun()

def safe(value, fallback="—"):
    return value if value not in (None, "", []) else fallback

def company_name(company):
    return safe(company.get("name"), safe(company.get("company_name"), "Unknown organisation"))

def company_address(company):
    value = company.get("address", "")
    if isinstance(value, dict):
        pieces = [
            value.get("address_line_1"),
            value.get("locality"),
            value.get("region"),
            value.get("postal_code"),
        ]
        return ", ".join(str(x) for x in pieces if x)
    return safe(value, st.session_state.selected_location)

def market_total():
    return len(st.session_state.market_results)

def active_total():
    return sum(1 for x in st.session_state.market_results if x.get("status") == "active")

def app_topbar():
    c1, c2, c3, c4, c5 = st.columns([6.2, .6, .6, .6, .75])
    with c1:
        global_query = st.text_input(
            "Global search",
            placeholder="Search your market or ask REACH AI...",
            label_visibility="collapsed",
            key=f"global_search_{st.session_state.page}",
        )
    with c2:
        if st.button("＋", key=f"top_add_{st.session_state.page}", help="Create new", use_container_width=True):
            nav_to("Enter Product")
    with c3:
        if st.button("✦", key=f"top_ai_{st.session_state.page}", help="REACH AI", use_container_width=True):
            nav_to("AI")
    with c4:
        if st.button("◌", key=f"top_notifications_{st.session_state.page}", help="Notifications", use_container_width=True):
            nav_to("Notifications")
    with c5:
        if st.button("AD", key=f"top_account_{st.session_state.page}", help="Settings", use_container_width=True):
            nav_to("Settings")

def sidebar():
    if st.session_state.page in ("Landing", "Auth"):
        return
    if not DEMO_MODE and not st.session_state.get("auth_user"):
        require_auth(st.session_state.page)

    # Internal REACH app: render the persistent navigation on every workspace.
    st.markdown('<div id="reach-internal-app"></div>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('<div class="side-logo">REACH<span class="dot">.</span></div>', unsafe_allow_html=True)
        st.caption(st.session_state.get("workspace_name") or "REACH Workspace")
        page = st.session_state.page

        def btn(label, target, icon="", key_suffix=None):
            unique_key = key_suffix or label.lower().replace(" ", "_").replace("&", "and")
            if st.button(
                f"{icon}  {label}",
                key=f"side_{unique_key}",
                type="primary" if page == target else "secondary",
                use_container_width=True,
            ):
                nav_to(target)

        btn("Home", "Home", "⌂", "home")
        btn("REACH AI", "AI", "✦", "reach_ai")

        st.markdown('<div class="side-label">PROSPECT & ENRICH</div>', unsafe_allow_html=True)
        btn("Search", "Companies", "⌕", "search")
        btn("Companies", "Companies", "▦", "companies")
        btn("People", "People", "♙", "people")
        btn("Lists", "Lists", "☷", "lists")
        btn("Saved Searches", "Saved Searches", "⌕", "saved_searches")
        btn("Saved People", "Saved People", "♙", "saved_people")
        btn("Saved Companies", "Saved Companies", "▦", "saved_companies")
        btn("Personas", "Personas", "◎", "personas")
        btn("Scores", "Scores", "★", "scores")
        btn("Territories", "Territories", "⌖", "territories")
        btn("Market Coverage", "Market Coverage", "◉", "market_coverage")
        btn("Market Map", "Market Map", "⌖", "market_map")
        btn("Market Memory", "Market Memory", "◇", "market_memory")

        st.markdown('<div class="side-label">ENGAGE</div>', unsafe_allow_html=True)
        btn("Sequences", "Outreach", "➤", "sequences")
        btn("Emails", "Emails", "✉", "emails")
        btn("Calls", "Calls", "☎", "calls")
        btn("Tasks", "Tasks", "☑", "tasks")
        btn("Templates", "Templates", "▣", "templates")
        btn("Workflows", "Workflows", "♦", "workflows")
        btn("Playbooks", "Playbooks", "▷", "playbooks")

        st.markdown('<div class="side-label">WIN DEALS</div>', unsafe_allow_html=True)
        btn("Meetings", "Meetings", "▣", "meetings")
        btn("Conversations", "Conversations", "◉", "conversations")
        btn("Deals", "Opportunities", "●", "deals")
        btn("Pipeline", "Pipeline", "⌘", "pipeline")

        st.markdown('<div class="side-label">RESEARCH & ENRICHMENT</div>', unsafe_allow_html=True)
        btn("Market Insights", "Market Ready", "✦", "market_insights")
        btn("Research", "Research", "◎", "research")
        btn("Technologies", "Technologies", "▧", "technologies")
        btn("Funding", "Funding", "◌", "funding")
        btn("News & Triggers", "News & Triggers", "⚡", "news_triggers")
        btn("Signals", "Signals", "⌁", "signals")

        st.markdown('<div class="side-label">ANALYTICS</div>', unsafe_allow_html=True)
        btn("Analytics", "Analytics", "▥", "analytics")
        btn("Reports", "Reports", "▤", "reports")
        btn("Activity", "Activity", "◉", "activity")
        btn("Team Performance", "Team Performance", "♧", "team_performance")

        st.markdown('<div class="side-label">PLATFORM</div>', unsafe_allow_html=True)
        btn("Integrations", "Integrations", "⌘", "integrations")
        btn("Data Quality", "Data Quality", "✓", "data_quality")
        btn("Enrichment", "Enrichment", "✦", "enrichment")
        btn("Custom Fields", "Custom Fields", "≡", "custom_fields")
        btn("Suppression List", "Suppression List", "⊘", "suppression")
        btn("Notifications", "Notifications", "◌", "notifications")

        st.markdown("""
        <div class="side-market" style="border-color:rgba(45,245,138,.28);">
          <b style="color:#2df58a">♛ &nbsp; Upgrade</b>
          <p>Unlock more research, outreach and automation.</p>
          <div class="side-track"><i style="width:62%"></i></div>
        </div>
        """, unsafe_allow_html=True)

        btn("Settings", "Settings", "⚙", "settings")
        st.divider()
        st.caption(st.session_state.get("auth_email") or "Signed in")
        if st.button("↪  Sign out", key="side_sign_out", use_container_width=True):
            sign_out_reach()
        btn("Help & Support", "Help", "?", "help")

def page_header(eyebrow, title, subtitle):
    st.markdown(
        f'<div class="page-eyebrow">{eyebrow}</div>'
        f'<div class="page-title">{title}</div>'
        f'<div class="page-sub">{subtitle}</div>',
        unsafe_allow_html=True,
    )

# ============================================================
# SIDEBAR
# ============================================================

sidebar()

# ============================================================
# 01 — LANDING / HOOK
# ============================================================

# ============================================================
# GLOBAL INTERACTIVE STATE
# ============================================================
_INTERACTIVE_DEFAULTS = {
    "people_filter_open": True,
    "people_status": "Total",
    "outreach_step": "Personalised email",
    "call_view": "All calls",
    "task_view": "Today",
    "pipeline_view": "Board",
    "selected_task": None,
    "people_results": [],
    "people_search_errors": [],
    "people_has_searched": False,
    "enrichment_mode": "Saved records",
    "enrichment_target": "companies",
    "provider_setup_for": None,
}
for _k, _v in _INTERACTIVE_DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ============================================================
# LOCATION / DISTANCE HELPERS
# ============================================================
UK_POSTCODE_AREA_CENTROIDS = {
    "E": (51.5450,-0.0553),"EC":(51.5155,-0.0922),"N":(51.5900,-0.1050),"NW":(51.5550,-0.2050),
    "SE":(51.4550,-0.0400),"SW":(51.4500,-0.1700),"W":(51.5130,-0.2150),"WC":(51.5180,-0.1200),
    "IG":(51.5650,0.0700),"RM":(51.5750,0.1800),"BR":(51.4050,0.0150),"CR":(51.3700,-0.1000),
    "KT":(51.3650,-0.2850),"TW":(51.4450,-0.3400),"UB":(51.5200,-0.4500),"HA":(51.5800,-0.3400),
    "EN":(51.6500,-0.0800),"DA":(51.4450,0.2200),"SM":(51.3600,-0.1900),"AL":(51.7500,-0.3300),
    "CM":(51.7350,0.4700),"SS":(51.5450,0.7050),"SG":(51.9000,-0.2000),"LU":(51.8800,-0.4200),
    "HP":(51.7500,-0.7000),"MK":(52.0400,-0.7600),"OX":(51.7500,-1.2600),"RG":(51.4550,-0.9700),
    "GU":(51.2350,-0.5750),"BN":(50.8300,-0.1400),"RH":(51.1200,-0.1800),"TN":(51.1350,0.2700),
    "ME":(51.3800,0.5200),"CT":(51.2800,1.0800),"B":(52.4862,-1.8904),"CV":(52.4050,-1.5100),
    "DY":(52.5100,-2.0800),"WS":(52.5850,-1.9800),"WV":(52.5900,-2.1300),"LE":(52.6369,-1.1398),
    "NG":(52.9548,-1.1581),"DE":(52.9225,-1.4746),"NN":(52.2405,-0.9027),"M":(53.4808,-2.2426),
    "L":(53.4084,-2.9916),"WA":(53.3900,-2.5900),"WN":(53.5450,-2.6300),"BL":(53.5800,-2.4300),
    "OL":(53.5400,-2.1100),"SK":(53.4100,-2.1600),"PR":(53.7632,-2.7031),"BB":(53.7500,-2.4800),
    "LS":(53.8008,-1.5491),"BD":(53.7950,-1.7600),"HD":(53.6450,-1.7800),"HX":(53.7200,-1.8600),
    "WF":(53.6800,-1.5000),"S":(53.3811,-1.4701),"YO":(53.9590,-1.0815),"HU":(53.7676,-0.3274),
    "DN":(53.5228,-1.1285),"NE":(54.9783,-1.6178),"DH":(54.7750,-1.5750),"SR":(54.9069,-1.3838),
    "TS":(54.5742,-1.2350),"DL":(54.5250,-1.5550),"CA":(54.8950,-2.9350),"LA":(54.0470,-2.8010),
    "BS":(51.4545,-2.5879),"BA":(51.3811,-2.3590),"GL":(51.8642,-2.2382),"SN":(51.5600,-1.7800),
    "SP":(51.0700,-1.8000),"SO":(50.9097,-1.4044),"PO":(50.8198,-1.0880),"BH":(50.7192,-1.8808),
    "DT":(50.7100,-2.4400),"EX":(50.7184,-3.5339),"PL":(50.3755,-4.1427),"TQ":(50.4619,-3.5253),
    "TA":(51.0153,-3.1030),"TR":(50.2632,-5.0510),"CF":(51.4816,-3.1791),"NP":(51.5842,-2.9977),
    "SA":(51.6214,-3.9436),"SY":(52.7073,-2.7553),"LL":(53.1900,-3.0400),"CH":(53.1900,-2.8900),
    "EH":(55.9533,-3.1883),"G":(55.8642,-4.2518),"FK":(56.0000,-3.7800),"KY":(56.1200,-3.1600),
    "DD":(56.4620,-2.9707),"PH":(56.3950,-3.4300),"AB":(57.1497,-2.0943),"IV":(57.4778,-4.2247),
    "PA":(55.8450,-4.4250),"BT":(54.5973,-5.9301)
}
CITY_CENTROIDS = {
    "london":(51.5074,-0.1278),"ilford":(51.5590,0.0741),"birmingham":(52.4862,-1.8904),
    "manchester":(53.4808,-2.2426),"liverpool":(53.4084,-2.9916),"leeds":(53.8008,-1.5491),
    "sheffield":(53.3811,-1.4701),"bristol":(51.4545,-2.5879),"cardiff":(51.4816,-3.1791),
    "edinburgh":(55.9533,-3.1883),"glasgow":(55.8642,-4.2518),"belfast":(54.5973,-5.9301),
    "nottingham":(52.9548,-1.1581),"leicester":(52.6369,-1.1398),"newcastle":(54.9783,-1.6178),
    "southampton":(50.9097,-1.4044),"brighton":(50.8225,-0.1372),"oxford":(51.7520,-1.2577),
    "cambridge":(52.2053,0.1218)
}

def haversine_miles(a, b):
    lat1, lon1 = a; lat2, lon2 = b
    r = 3958.7613
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(math.sqrt(h))

def postcode_area(value):
    matches = re.findall(r"\b([A-Z]{1,2})\d[A-Z\d]?\b", str(value or "").upper())
    return matches[-1] if matches else None

def approximate_coords(value):
    low = str(value or "").lower()
    for city, coords in CITY_CENTROIDS.items():
        if city in low:
            return coords
    return UK_POSTCODE_AREA_CENTROIDS.get(postcode_area(value))

def company_distance(company, origin):
    dest = approximate_coords(company_address(company))
    return haversine_miles(origin, dest) if origin and dest else None




# ============================================================
# PORTFOLIO DEMO SAFETY LAYER
# ============================================================
# These overrides keep the public build self-contained. Nothing here writes
# to Supabase or any other external service.
if DEMO_MODE:
    def save_product_and_strategy(analysis):
        st.session_state.product_id = "demo-product"
        st.session_state.strategy_id = "demo-strategy"
        return "demo-product", "demo-strategy"

    def save_discovered_companies(companies):
        st.session_state.market_results = list(companies or [])
        st.session_state.market_built = bool(st.session_state.market_results)
        return len(st.session_state.market_results)

    def load_saved_companies():
        return list(st.session_state.get("market_results") or [])

    def load_saved_market_context():
        return bool(st.session_state.get("analysis"))

    def ensure_saved_company_memberships():
        return 0

    def load_reach_workspace():
        st.session_state.workspace_id = "demo-workspace"
        st.session_state.workspace_name = "Portfolio Demo Workspace"
        return st.session_state.workspace_id

# Authenticated users belong in the private workspace. If Streamlit reruns with
# a stale public-page value, recover to Home instead of showing Landing again.
if st.session_state.get("auth_user") and st.session_state.page in ("Landing", "Auth"):
    st.session_state.page = "Home"

if st.session_state.page == "Auth":
    render_auth_page()

elif st.session_state.page == "Landing":
    st.info("Portfolio Demo · Uses sample data only. No external AI, enrichment or contact APIs are called.")
    # ============================================================
    # REACH — ANIMATED PREMIUM LANDING PAGE
    # ============================================================

    st.markdown("""
    <style>
    /* Landing has no sidebar, so remove the authenticated workspace offset. */
    [data-testid="stAppViewContainer"] > .main,
    [data-testid="stMain"],
    .stMain{
        margin-left:0 !important;
        padding-left:0 !important;
        width:100% !important;
        max-width:100% !important;
    }
    [data-testid="stMainBlockContainer"],
    .block-container{
        margin-left:auto !important;
        margin-right:auto !important;
        padding-left:0 !important;
        padding-right:0 !important;
        width:100% !important;
        max-width:100% !important;
    }
    :root{--g:#3cf08e;--g2:#73f7b0;--bg:#020805;--card:#08140e;--line:rgba(95,240,156,.25);--muted:#98a39d}
    html,body,[class*="css"]{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
    .stApp{background:radial-gradient(circle at 0 25%,rgba(0,255,122,.18),transparent 25%),radial-gradient(circle at 100% 22%,rgba(0,255,122,.16),transparent 25%),linear-gradient(180deg,#020805,#010604);color:#fff}
    [data-testid="stHeader"]{background:transparent;height:0}.block-container{max-width:1180px;padding-top:.7rem;padding-bottom:4rem}footer{visibility:hidden}
    .nav{display:grid;grid-template-columns:230px 1fr 240px;align-items:center;padding:12px 0 28px}.brand{font-size:26px;font-weight:900}.brand b{color:var(--g)}.tag{color:var(--g);font-size:10px}.links{display:flex;justify-content:center;gap:28px;font-size:12px;color:#e2e7e4}.actions{text-align:right;font-size:12px}.signup{display:inline-block;margin-left:18px;padding:12px 18px;border-radius:18px;background:linear-gradient(135deg,var(--g2),var(--g));color:#031008;font-weight:850}
    .hero{text-align:center;padding:30px 0 18px}.kicker{color:var(--g);font-size:10px;font-weight:900;letter-spacing:4px;margin-bottom:18px}.title{font-size:clamp(50px,5.7vw,72px);font-weight:900;line-height:1.02;letter-spacing:-3.5px}.title b{color:var(--g)}.sub{max-width:790px;margin:20px auto 5px;color:#a1aca5;font-size:15px;line-height:1.6}
    .demo-label{text-align:center;color:var(--g);font-size:10px;font-weight:900;letter-spacing:3px;margin:12px 0 7px}
    .stTextArea textarea{background:#08140e!important;color:#fff!important;border:1px solid rgba(74,242,145,.55)!important;border-radius:24px!important;min-height:65px!important;height:65px!important;resize:none!important}
    .stTextInput input,[data-baseweb="select"]>div{background:#09140e!important;color:#fff!important;border:1px solid rgba(255,255,255,.12)!important;border-radius:13px!important}
    label{color:#8d9992!important;font-size:11px!important}
    .stButton>button[kind="primary"]{background:linear-gradient(135deg,var(--g2),var(--g))!important;color:#031008!important;border:0!important;border-radius:18px!important;min-height:46px;font-weight:900!important}
    .search-title{text-align:center;font-size:22px;font-weight:850;margin:30px 0 7px}.search-copy{text-align:center;color:#8f9b94;font-size:12px;margin-bottom:14px}
    .chips{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;margin:12px 0 22px}.chip{border:1px solid rgba(255,255,255,.17);border-radius:999px;padding:7px 12px;color:#d6ded9;font-size:10px}
    .ind-title{font-size:15px;font-weight:850;margin-top:28px}.ind-copy{font-size:11px;color:#8e9993;margin:4px 0 12px}.industries{display:grid;grid-template-columns:repeat(10,1fr);gap:8px}.industry{border:1px solid var(--line);border-radius:9px;background:#08140e;text-align:center;padding:12px 5px;min-height:66px}.ii{font-size:19px;margin-bottom:7px}.in{font-size:8px}
    .benefits{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin-top:28px;padding-top:18px;border-top:1px solid rgba(255,255,255,.06)}.benefit{font-size:11px;color:#e6ebe8}.benefit b{display:block;font-size:12px;margin-bottom:6px}.benefit span{color:#87938c;line-height:1.5}
    .welcome{color:var(--g);font-size:10px;font-weight:900;letter-spacing:3px;text-transform:uppercase}.ready-box{background:rgba(49,233,129,.08);border:1px solid rgba(49,233,129,.22);border-radius:14px;padding:16px;color:#c0f8d7}
    [data-testid="stVerticalBlockBorderWrapper"]{background:#08140e;border-color:rgba(255,255,255,.09)!important;border-radius:15px!important}div[data-testid="stMetric"]{background:#09140e;border:1px solid rgba(255,255,255,.08);padding:15px;border-radius:13px}div[data-testid="stMetricValue"]{color:#fff!important}
    h1,h2,h3,h4,p,li,.stMarkdown{color:#f0f4f2}hr{border-color:rgba(255,255,255,.07)!important}
    @media(max-width:900px){.nav{grid-template-columns:1fr auto}.links{display:none}.industries{grid-template-columns:repeat(5,1fr)}}

    /* Premium real-search section */
    .real-search-wrap{max-width:930px;margin:38px auto 6px;text-align:center}
    .real-search-wrap h2{font-size:25px!important;letter-spacing:-.7px;margin:0 0 7px!important}
    .real-search-wrap p{font-size:12px;color:#89968f;margin:0 0 18px}
    [data-testid="stTextArea"]{max-width:930px;margin:auto}
    [data-testid="stTextArea"] textarea{
     background:linear-gradient(180deg,#07130d,#06100b)!important;
     border:1px solid rgba(69,239,143,.42)!important;
     box-shadow:inset 0 0 0 1px rgba(255,255,255,.025),0 10px 35px rgba(0,0,0,.18)!important;
     border-radius:16px!important;
     min-height:58px!important;height:58px!important;
     padding:18px 20px!important;font-size:13px!important;
    }
    [data-testid="stTextArea"] textarea:focus{border-color:#43ef91!important;box-shadow:0 0 0 2px rgba(67,239,145,.08)!important}
    [data-testid="stTextArea"] textarea::placeholder{color:#5f6d65!important}
    .real-search-meta{max-width:930px;margin:8px auto 0}
    div[data-testid="stSelectbox"]>div>div,
    div[data-testid="stTextInput"] input{
     background:#07120c!important;border:1px solid rgba(255,255,255,.13)!important;
     border-radius:12px!important;min-height:43px!important;color:#e8eeeb!important;
     box-shadow:none!important
    }
    div[data-testid="stSelectbox"]>div>div:focus-within,
    div[data-testid="stTextInput"] input:focus{border-color:rgba(67,239,145,.55)!important}
    .real-find [data-testid="stButton"] button{
     max-width:930px!important;margin:4px auto 0!important;border-radius:13px!important;
     min-height:47px!important;font-size:12px!important;letter-spacing:.1px;
     box-shadow:0 8px 28px rgba(47,238,135,.12)!important
    }

    .find-shell{max-width:980px;margin:34px auto 10px;padding:28px 30px 18px;border:1px solid rgba(70,241,145,.25);border-radius:24px;background:radial-gradient(circle at 12% 0%,rgba(57,239,141,.12),transparent 32%),radial-gradient(circle at 92% 100%,rgba(72,145,255,.08),transparent 30%),linear-gradient(145deg,#08150e,#041009);box-shadow:0 24px 70px rgba(0,0,0,.34),inset 0 1px 0 rgba(255,255,255,.025);position:relative;overflow:hidden}
    .find-eyebrow{display:inline-flex;align-items:center;gap:7px;color:#5df3a0;font-size:9px;font-weight:900;letter-spacing:2.4px}.find-eyebrow i{width:7px;height:7px;border-radius:50%;background:#3cf08e;box-shadow:0 0 14px #3cf08e}
    .find-head{display:grid;grid-template-columns:1.2fr .8fr;gap:22px;align-items:end;margin:8px 0 20px}.find-head h2{font-size:30px!important;line-height:1.05!important;letter-spacing:-1.1px!important;margin:0!important}.find-head h2 b{color:#4df19a}.find-head p{font-size:11px!important;line-height:1.55!important;color:#8f9c94!important;margin:0!important}
    .find-label{max-width:930px;margin:0 auto 7px;color:#cbd5cf;font-size:10px;font-weight:750}.find-label span{color:#55f19d}.search-hint{max-width:930px;margin:9px auto 12px;display:flex;align-items:center;justify-content:space-between;color:#718078;font-size:8px}.search-hint b{color:#9aa69f}
    .example-row{display:flex;gap:7px;flex-wrap:wrap;justify-content:center;margin:15px 0 2px}.example-pill{padding:7px 10px;border-radius:999px;background:#07120c;border:1px solid rgba(255,255,255,.09);color:#9ba79f;font-size:8px}.example-pill strong{color:#55f19d}
    .mini-proof{max-width:980px;margin:12px auto 0;display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.proof{padding:11px 12px;border-radius:12px;background:rgba(7,18,12,.75);border:1px solid rgba(255,255,255,.065);font-size:8px;color:#829087}.proof b{display:block;color:#dce5df;font-size:9px;margin-bottom:3px}.proof em{font-style:normal;color:#4ff19b}
    @media(max-width:800px){.find-head{grid-template-columns:1fr}.mini-proof{grid-template-columns:1fr}.find-shell{padding:22px 16px}.find-head h2{font-size:25px!important}}

    </style>
    """, unsafe_allow_html=True)

    st.markdown("""<div class="nav"><div><div class="brand">◉ REACH<b>.</b></div><div class="tag">Turn your market green.</div></div><div class="links"><span>Product</span><span>How it works</span><span>Solutions⌄</span><span>Resources⌄</span><span>Pricing</span></div><div class="actions">Secure workspace</div></div>
    <div class="hero"><div class="kicker">AI-POWERED MARKET DEVELOPMENT</div><div class="title">Your customers are out there.<br><b>REACH</b> finds them.</div><div class="sub">Tell REACH about your product, service or business. It discovers relevant organisations, researches who to reach, helps contact them and tracks every opportunity — all in one place.</div></div>
    <div class="demo-label">SEE REACH IN ACTION</div>""", unsafe_allow_html=True)

    auth_left, auth_signin, auth_signup, auth_right = st.columns([3.2, 1, 1.35, 3.2])
    with auth_signin:
        if st.button("Explore demo", key="landing_sign_in", use_container_width=True):
            st.session_state.page = "Home"
            st.rerun()
    with auth_signup:
        if st.button("Open portfolio demo →", key="landing_sign_up", type="primary", use_container_width=True):
            st.session_state.page = "Home"
            st.rerun()

    # Animated demo is deliberately before the real search form.
    st.html(r"""
    <!doctype html><html><head><style>
    *{box-sizing:border-box}body{margin:0;background:transparent;color:#f5f8f6;font-family:Inter,Arial,sans-serif;overflow:hidden}
    :root{--g:#39ef8d;--g2:#74f7b1;--blue:#50a9ff;--yellow:#ffd34f;--purple:#bba5ff}
    .stage{
        display:grid;
        grid-template-columns:145px minmax(0,760px) 145px;
        gap:16px;
        align-items:center;
        justify-content:center;
        width:min(100%,1082px);
        max-width:1082px;
        margin:0 auto;
        padding:0 10px;
    }
    .stack{display:flex;flex-direction:column;gap:18px}
    .call{position:relative;border:1px solid rgba(75,239,143,.28);background:linear-gradient(180deg,#08150e,#041008);border-radius:14px;padding:14px;min-height:142px}
    .ico{width:38px;height:38px;border-radius:50%;display:grid;place-items:center;background:rgba(57,239,141,.13);color:var(--g);font-size:19px;margin-bottom:10px}.ct{font-size:13px;font-weight:850;line-height:1.18;margin-bottom:7px}.cc{font-size:9px;color:#93a099;line-height:1.45}
    .arrow{position:absolute;top:50%;width:42px;height:2px;background:linear-gradient(90deg,transparent,var(--g));animation:pulse 1.4s ease-in-out infinite}.left .arrow{right:-43px}.right .arrow{left:-43px;transform:rotate(180deg)}.arrow:after{content:"";position:absolute;right:-1px;top:-4px;width:8px;height:8px;border-top:2px solid var(--g);border-right:2px solid var(--g);transform:rotate(45deg)}
    .shell{
        width:100%;
        max-width:760px;
        margin:0 auto;
        border:1px solid #37e986;
        border-radius:18px;
        background:linear-gradient(180deg,#06120b,#030a06);
        padding:8px;
        box-shadow:0 24px 70px rgba(0,0,0,.4)
    }
    .window{border:1px solid rgba(255,255,255,.1);border-radius:12px;overflow:hidden;display:grid;grid-template-columns:112px 1fr;min-height:485px}.side{border-right:1px solid rgba(255,255,255,.08);padding:14px 9px}.logo{font-size:14px;font-weight:900;margin-bottom:18px}.logo b{color:var(--g)}.nav{font-size:8px;color:#aab4ae;padding:8px 6px;border-radius:6px;margin:3px 0}.nav.active{background:rgba(40,232,123,.15);color:#67f4a4}
    .main{padding:14px;position:relative}.top{display:flex;justify-content:space-between;align-items:center}.top h2{font-size:17px;margin:0}.live{font-size:8px;border:1px solid rgba(57,239,141,.35);border-radius:999px;padding:5px 7px;color:#79f7af}
    .search{height:48px;border:1px solid rgba(57,239,141,.5);border-radius:10px;margin:10px 0;display:flex;align-items:center;padding-left:10px;background:#09160f;overflow:hidden}.typed{font-size:9px;white-space:nowrap;overflow:hidden;width:0;border-right:1px solid var(--g);animation:type 16s steps(68,end) infinite,blink .7s step-end infinite}.find{margin-left:auto;height:100%;min-width:112px;display:grid;place-items:center;background:linear-gradient(135deg,var(--g2),var(--g));color:#021008;font-size:8px;font-weight:900;position:relative}.find:after{content:"Building market…";position:absolute;inset:0;display:grid;place-items:center;background:linear-gradient(135deg,var(--g2),var(--g));opacity:0;animation:button 16s infinite}
    .steps{display:grid;grid-template-columns:repeat(7,1fr);gap:3px;margin:9px 0}.step{text-align:center;font-size:5.9px;color:#78847d}.circle{width:17px;height:17px;border-radius:50%;display:grid;place-items:center;background:#16221b;color:#91a098;margin:0 auto 3px}.s1 .circle{animation:on 16s 3.6s infinite}.s2 .circle{animation:on 16s 5s infinite}.s3 .circle{animation:on 16s 6.3s infinite}.s4 .circle{animation:on 16s 7.5s infinite}.s5 .circle{animation:on 16s 8.7s infinite}.s6 .circle{animation:on 16s 10s infinite}.s7 .circle{animation:on 16s 12.4s infinite}
    .loading{height:26px;border:1px solid rgba(57,239,141,.22);border-radius:7px;background:rgba(57,239,141,.05);display:flex;align-items:center;padding:0 8px;gap:7px;margin:7px 0;font-size:7px;color:#aab4ae}.spin{width:13px;height:13px;border:2px solid rgba(57,239,141,.2);border-top-color:var(--g);border-radius:50%;animation:spin .7s linear infinite}
    .metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:7px 0}.metric{border:1px solid rgba(255,255,255,.07);background:#0a1710;border-radius:8px;padding:7px}.val{font-size:14px;font-weight:900;color:var(--g)}.lab{font-size:6px;color:#89958e}.num:after{content:"0";animation:count 16s infinite}.n2:after{animation-name:count2}.n3:after{animation-name:count3}.n4:after{animation-name:count4}
    .content{display:grid;grid-template-columns:1.08fr .92fr;gap:8px}.table{border:1px solid rgba(255,255,255,.07);border-radius:8px;overflow:hidden}.row{display:grid;grid-template-columns:1.2fr .72fr .66fr;gap:4px;padding:7px;border-top:1px solid rgba(255,255,255,.05);font-size:6.4px;opacity:0}.head{opacity:1;color:#78857d}.r1{animation:row 16s 5.5s infinite}.r2{animation:row 16s 6.2s infinite}.r3{animation:row 16s 6.9s infinite}.r4{animation:row 16s 7.6s infinite}.org{font-weight:700}.status{border-radius:999px;padding:3px;text-align:center}.ready{background:rgba(26,137,255,.15);color:var(--blue)}.sent{background:rgba(255,199,40,.14);color:var(--yellow)}.green{background:rgba(44,235,130,.15);color:#63f5a3}
    .outreach{border:1px solid rgba(57,239,141,.25);border-radius:8px;background:#08140e;padding:8px}.out-title{font-size:8px;font-weight:850}.email{margin-top:6px;border:1px solid rgba(255,255,255,.07);border-radius:7px;padding:7px;font-size:6.3px;color:#aab4ae;line-height:1.4;height:100px;opacity:.25;animation:email 16s infinite}.send{margin-top:6px;background:linear-gradient(135deg,var(--g2),var(--g));color:#031008;text-align:center;border-radius:7px;padding:7px;font-size:7px;font-weight:900;opacity:.3;animation:send 16s infinite}.reply{margin-top:6px;border:1px solid rgba(57,239,141,.22);border-radius:7px;padding:6px;background:rgba(57,239,141,.06);opacity:0;animation:reply 16s infinite}.reply b,.reply strong{color:var(--g);font-size:7px}.reply p{font-size:6.2px;margin:3px 0}
    .cursor{position:absolute;z-index:20;filter:drop-shadow(0 2px 2px #000);animation:cursor 16s infinite}.cursor:before{content:"";display:block;width:0;height:0;border-top:15px solid white;border-right:9px solid transparent;transform:rotate(-15deg)}
    .click{position:absolute;width:24px;height:24px;border:1px solid var(--g);border-radius:50%;opacity:0;z-index:19;animation:click 16s infinite}
    @keyframes type{0%,4%{width:0}18%,100%{width:330px}}@keyframes blink{50%{border-color:transparent}}@keyframes button{0%,20%{opacity:0}22%,36%{opacity:1}38%,100%{opacity:0}}
    @keyframes spin{to{transform:rotate(360deg)}}@keyframes pulse{50%{opacity:.35}}@keyframes on{0%,8%{background:#16221b;color:#91a098}12%,80%{background:var(--g);color:#031008}86%,100%{background:#16221b;color:#91a098}}
    @keyframes row{0%,8%{opacity:0;transform:translateY(4px)}12%,78%{opacity:1;transform:none}88%,100%{opacity:0}}
    @keyframes email{0%,50%{opacity:.25}58%,90%{opacity:1}100%{opacity:.25}}@keyframes send{0%,58%{opacity:.3}62%,84%{opacity:1}100%{opacity:.3}}@keyframes reply{0%,75%{opacity:0;transform:translateY(4px)}80%,92%{opacity:1;transform:none}100%{opacity:0}}
    @keyframes count{0%,28%{content:"0"}36%{content:"184"}44%{content:"623"}52%,92%{content:"1,247"}100%{content:"0"}}@keyframes count2{0%,38%{content:"0"}48%{content:"315"}56%,92%{content:"892"}100%{content:"0"}}@keyframes count3{0%,60%{content:"0"}68%{content:"57"}76%,92%{content:"214"}100%{content:"0"}}@keyframes count4{0%,76%{content:"0"}84%,92%{content:"68"}100%{content:"0"}}
    @keyframes cursor{0%{left:28%;top:64px}17%{left:52%;top:64px}20%{left:88%;top:64px}23%{left:88%;top:64px}42%{left:42%;top:290px}57%{left:76%;top:310px}65%{left:85%;top:365px}78%{left:82%;top:414px}100%{left:28%;top:64px}}
    @keyframes click{0%,19%{opacity:0;left:87%;top:57px;transform:scale(.3)}20%{opacity:1;left:87%;top:57px;transform:scale(1.5)}22%,100%{opacity:0;left:87%;top:57px;transform:scale(2)}}
    @media(max-width:900px){.stage{grid-template-columns:1fr}.stack{display:grid;grid-template-columns:1fr 1fr}.arrow{display:none}.window{grid-template-columns:1fr}.side{display:none}}
    </style></head><body>
    <div class="stage">
    <div class="stack">
    <div class="call left"><div class="ico">⌕</div><div class="ct">Find relevant organisations</div><div class="cc">Instead of manually searching, REACH builds the relevant market for you.</div><div class="arrow"></div></div>
    <div class="call left"><div class="ico">◎</div><div class="ct">Research automatically</div><div class="cc">It researches organisations and finds appropriate decision-makers and contact routes.</div><div class="arrow"></div></div>
    </div>
    <div class="shell"><div class="window">
    <div class="side"><div class="logo">◉ REACH<b>.</b></div><div class="nav active">⌂ &nbsp; Home</div><div class="nav">◎ &nbsp; My Markets</div><div class="nav">✉ &nbsp; Outreach</div><div class="nav">● &nbsp; Opportunities</div><div class="nav">▥ &nbsp; Analytics</div></div>
    <div class="main"><div class="cursor"></div><div class="click"></div>
    <div class="top"><h2>See what happens after you press Find my market</h2><div class="live">● LIVE DEMO</div></div>
    <div class="search"><div class="typed">AI tool that records veterinary consultations and creates clinical notes</div><div class="find">Find my market →</div></div>
    <div class="steps"><div class="step s1"><div class="circle">1</div>Understand</div><div class="step s2"><div class="circle">2</div>Discover</div><div class="step s3"><div class="circle">3</div>Research</div><div class="step s4"><div class="circle">4</div>Find contacts</div><div class="step s5"><div class="circle">5</div>Personalise</div><div class="step s6"><div class="circle">6</div>Contact</div><div class="step s7"><div class="circle">7</div>Track replies</div></div>
    <div class="loading"><div class="spin"></div><span>REACH is finding, researching and working through your approved market…</span></div>
    <div class="metrics"><div class="metric"><div class="val num"></div><div class="lab">Organisations discovered</div></div><div class="metric"><div class="val num n2"></div><div class="lab">Verified contacts</div></div><div class="metric"><div class="val num n3"></div><div class="lab">Contacted</div></div><div class="metric"><div class="val num n4"></div><div class="lab">Interested</div></div></div>
    <div class="content"><div class="table"><div class="row head"><span>Organisation</span><span>Contact</span><span>Status</span></div><div class="row r1"><span class="org">Greenfield Veterinary Group</span><span>Practice Manager</span><span class="status ready">Ready</span></div><div class="row r2"><span class="org">Paws & Claws Clinics</span><span>Director</span><span class="status sent">Contacted ✓</span></div><div class="row r3"><span class="org">The Village Vet</span><span>Owner</span><span class="status green">Interested ✓</span></div><div class="row r4"><span class="org">Willowbrook Vets</span><span>Practice Manager</span><span class="status sent">Contacted ✓</span></div></div>
    <div class="outreach"><div class="out-title">✉ REACH is contacting your market for you</div><div class="email"><b>Personalising for Greenfield Veterinary Group…</b><br><br>Hi there,<br><br>I noticed your veterinary team focuses on high-quality patient care. Our AI consultation tool helps reduce time spent creating clinical notes...</div><div class="send">✓ Personalised outreach sent automatically</div><div class="reply"><b>● NEW REPLY</b><p>“This looks useful — we'd like to learn more.”</p><strong>✓ Opportunity turned green</strong></div></div></div>
    </div></div></div>
    <div class="stack">
    <div class="call right"><div class="ico">➤</div><div class="ct">Reach them for you</div><div class="cc"><b style="color:#72f5ae">The key gap:</b> REACH doesn't hand you a lead list and leave the manual work to you. It works through approved outreach.</div><div class="arrow"></div></div>
    <div class="call right"><div class="ico">●</div><div class="ct">Turn opportunities green</div><div class="cc">REACH tracks responses so interested organisations become clear opportunities to follow up.</div><div class="arrow"></div></div>
    </div></div>
    </body></html>
    """)

    st.markdown("""
        <div class="market-entry-card">
          <div class="market-entry-top">
            <div class="market-entry-copy">
              <div class="market-entry-eyebrow"><span></span> START YOUR MARKET</div>
              <div class="market-entry-title">Tell us what you offer.<br><b>REACH does the searching.</b></div>
            </div>
            <div class="market-entry-benefits">
              <div class="market-benefit">
                <div class="market-benefit-icon">⌕</div>
                <div><strong>Find relevant organisations</strong><small>Built around what you actually sell</small></div>
              </div>
              <div class="market-benefit">
                <div class="market-benefit-icon">♙</div>
                <div><strong>Discover decision-makers</strong><small>Research the right people to reach</small></div>
              </div>
              <div class="market-benefit">
                <div class="market-benefit-icon">ϟ</div>
                <div><strong>Prepare tailored outreach</strong><small>Move opportunities forward in one workflow</small></div>
              </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    product_description = st.text_area(
        "Product description",
        placeholder="e.g. An AI tool that records veterinary consultations and creates clinical notes...",
        height=58,
        label_visibility="collapsed"
    )

    st.markdown('<div class="search-hint"><span>Be as simple or detailed as you like.</span><b>REACH analyses your market automatically ✦</b></div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1,1], gap="small")
    with c1:
        location = st.selectbox("◎  Where do you want to find customers?", ["United Kingdom","England","Scotland","Wales","Northern Ireland","London","Worldwide"])
    with c2:
        website = st.text_input("↗  Website (optional)", placeholder="Paste your website for extra context")

    st.markdown('<div class="real-find">', unsafe_allow_html=True)
    find_market = st.button("✦  Find my market   →", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="example-row"><span class="example-pill"><strong>Try:</strong> AI veterinary notes</span><span class="example-pill"><strong>Try:</strong> Accountancy service</span><span class="example-pill"><strong>Try:</strong> Sustainable packaging</span><span class="example-pill"><strong>Try:</strong> Training course</span></div>
    <div class="mini-proof"><div class="proof"><b>01 · Understand</b>REACH works out <em>who is likely to need</em> what you offer.</div><div class="proof"><b>02 · Discover</b>It searches for relevant organisations instead of leaving you with manual research.</div><div class="proof"><b>03 · Work the market</b>Research, contact and opportunity tracking can then happen in one workflow.</div></div>
    """, unsafe_allow_html=True)

    st.markdown("""<div class="chips"><span class="chip">Products</span><span class="chip">Services</span><span class="chip">Businesses</span><span class="chip">Software</span><span class="chip">Agencies</span><span class="chip">Suppliers</span><span class="chip">Creators</span><span class="chip">and more</span></div>
    <div class="ind-title">Used across industries</div><div class="ind-copy">REACH works for products, services, businesses and more.</div>
    <div class="industries"><div class="industry"><div class="ii">✚</div><div class="in">Healthcare</div></div><div class="industry"><div class="ii">▣</div><div class="in">Professional Services</div></div><div class="industry"><div class="ii">♜</div><div class="in">Manufacturing</div></div><div class="industry"><div class="ii">▱</div><div class="in">Technology</div></div><div class="industry"><div class="ii">☕</div><div class="in">Hospitality</div></div><div class="industry"><div class="ii">♙</div><div class="in">Retail</div></div><div class="industry"><div class="ii">◆</div><div class="in">Education</div></div><div class="industry"><div class="ii">⌂</div><div class="in">Construction</div></div><div class="industry"><div class="ii">▥</div><div class="in">Finance</div></div><div class="industry"><div class="ii">•••</div><div class="in">and more</div></div></div>
    <div class="benefits"><div class="benefit"><b>◷ &nbsp; Save hours of manual work</b><span>Let REACH do the research, outreach and tracking for you.</span></div><div class="benefit"><b>♙ &nbsp; Find higher quality opportunities</b><span>Discover organisations that actually need what you do.</span></div><div class="benefit"><b>▥ &nbsp; Grow faster</b><span>Turn research into real conversations and customers.</span></div><div class="benefit"><b>◎ &nbsp; Focus on what matters</b><span>Spend less time searching and more time building relationships.</span></div></div>""", unsafe_allow_html=True)




    if find_market:
        if not product_description.strip():
            st.warning("Please describe your product, service or business first.")
        else:
            st.session_state.product_description = product_description
            st.session_state.selected_location = location
            st.session_state.website = website

            if not DEMO_MODE and not st.session_state.get("auth_user"):
                st.session_state.post_auth_page = "Home"
                st.session_state.page = "Auth"
                st.rerun()

            try:
                with st.spinner("REACH is understanding your market..."):
                    st.session_state.analysis = analyse_product(
                        description=product_description,
                        location=location,
                        website=website
                    )

                st.session_state.market_results = []
                st.session_state.market_built = False
                st.session_state.market_visible_count = 10
                nav_to("Market Ready")

            except Exception as e:
                st.error("REACH couldn't analyse your product right now.")
                st.caption("Check your OpenAI API connection and try again.")
                st.code(str(e))


# ============================================================
# REACH OPERATING HOME — Apollo-depth, REACH design
# ============================================================

elif st.session_state.page == "Home":
    app_topbar()
    total = market_total()
    discovered = total if total else 0

    st.markdown("""
    <div class="home-title">Welcome to REACH 👋</div>
    <div class="home-sub">Here's what's happening with your market, outreach and pipeline today.</div>
    """, unsafe_allow_html=True)

    st.html(f"""
    <div class="kpi6">
      <div class="kpi"><b>{discovered}</b><span>Organisations found</span></div>
      <div class="kpi"><b style="color:#70d8ff">0</b><span>Contacts found</span></div>
      <div class="kpi"><b style="color:#f3c84b">0</b><span>Contacted</span></div>
      <div class="kpi"><b style="color:#2df58a">0</b><span>Interested</span></div>
      <div class="kpi"><b style="color:#ff8790">0</b><span>Meetings booked</span></div>
      <div class="kpi"><b style="color:#f3c84b">0</b><span>Deals in pipeline</span></div>
    </div>

    <div class="home-grid">
      <section class="home-card">
        <div class="home-card-head"><h3>Recent activity</h3><a>View all →</a></div>
        <div class="mini-tabs"><span class="mini-tab on">All</span><span class="mini-tab">Emails</span><span class="mini-tab">Calls</span><span class="mini-tab">Meetings</span><span class="mini-tab">Replies</span></div>
        <div class="activity-item"><div class="act-icon">⌕</div><div><b>Your market workspace is ready</b><span>Build or continue researching your target market</span></div><em>Now</em></div>
        <div class="activity-item"><div class="act-icon">▦</div><div><b>{discovered} organisations discovered</b><span>Companies House market discovery</span></div><em>Today</em></div>
        <div class="activity-item"><div class="act-icon">➤</div><div><b>Outreach is waiting for contacts</b><span>Research decision-makers before launching</span></div><em>Next</em></div>
      </section>

      <section class="home-card">
        <div class="home-card-head"><h3>Tasks for today</h3><a>View all →</a></div>
        <div class="mini-tabs"><span class="mini-tab on">All</span><span class="mini-tab">Research</span><span class="mini-tab">Follow-ups</span></div>
        <div class="task-item"><div class="act-icon">☑</div><div><b>Review your market strategy</b><span>Confirm customer segments and search terms</span></div><em>09:30</em></div>
        <div class="task-item"><div class="act-icon">♙</div><div><b>Research decision-makers</b><span>Find the right people inside discovered organisations</span></div><em>11:00</em></div>
        <div class="task-item"><div class="act-icon">✉</div><div><b>Prepare outreach</b><span>Create your first personalised sequence</span></div><em>13:00</em></div>
        <div class="task-item"><div class="act-icon">▥</div><div><b>Review market coverage</b><span>See which segments still need discovery</span></div><em>16:00</em></div>
      </section>

      <section>
        <div class="home-card">
          <div class="home-card-head"><h3>Pipeline status</h3><a>View pipeline →</a></div>
          <div class="pipe-line"><span>🟢 Interested</span><b>0</b></div>
          <div class="pipe-line"><span>🔵 Meeting booked</span><b>0</b></div>
          <div class="pipe-line"><span>🟣 Proposal sent</span><b>0</b></div>
          <div class="pipe-line"><span>🟡 Negotiation</span><b>0</b></div>
          <div class="pipe-line"><span>● Closed won</span><b>0</b></div>
        </div>
      </section>

      <section class="home-card" style="grid-column:1/3">
        <div class="home-card-head"><h3>Recommended companies for you</h3><a>View all →</a></div>
        <div style="font-size:10px;color:#78877e">Based on your market strategy and discovery results.</div>
        <div class="recommend-table">
          <div class="rec-row head"><span>Company</span><span>Location</span><span>Status</span><span>Source</span><span>Fit</span><span>Action</span></div>
          <div class="rec-row"><strong>{company_name(st.session_state.market_results[0]) if st.session_state.market_results else "Build your first market"}</strong><span>{company_address(st.session_state.market_results[0]) if st.session_state.market_results else "United Kingdom"}</span><span>Discovered</span><span>Companies House</span><span class="fit">AI</span><span>Research →</span></div>
          <div class="rec-row"><strong>{company_name(st.session_state.market_results[1]) if len(st.session_state.market_results)>1 else "More recommendations will appear here"}</strong><span>{company_address(st.session_state.market_results[1]) if len(st.session_state.market_results)>1 else "—"}</span><span>Discovered</span><span>Companies House</span><span class="fit">AI</span><span>Research →</span></div>
          <div class="rec-row"><strong>{company_name(st.session_state.market_results[2]) if len(st.session_state.market_results)>2 else "REACH learns from your market"}</strong><span>{company_address(st.session_state.market_results[2]) if len(st.session_state.market_results)>2 else "—"}</span><span>Discovered</span><span>Companies House</span><span class="fit">AI</span><span>Research →</span></div>
        </div>
      </section>

      <section class="home-card">
        <div class="home-card-head"><h3>Quick actions</h3></div>
        <div class="quick-item"><span>▦</span><b>Find new companies</b><span>→</span></div>
        <div class="quick-item"><span>♙</span><b>Find decision-makers</b><span>→</span></div>
        <div class="quick-item"><span>➤</span><b>Start a sequence</b><span>→</span></div>
        <div class="quick-item"><span>⇧</span><b>Import a list</b><span>→</span></div>
        <div class="quick-item"><span>▣</span><b>Book a meeting</b><span>→</span></div>
      </section>
    </div>
    """)

# ============================================================
# 02 — ENTER PRODUCT
# ============================================================

elif st.session_state.page == "Enter Product":
    app_topbar()
    page_header(
        "START YOUR MARKET",
        "What do you want to find a market for?",
        "Describe what you offer. REACH will work out who could need it and how to find them.",
    )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    left, right = st.columns([1.35, .65], gap="medium")

    with left:
        with st.container(border=True):
            st.markdown("#### What do you offer?")
            description = st.text_area(
                "Description",
                value=st.session_state.product_description,
                placeholder="For example: AI software that records veterinary consultations and creates clinical notes...",
                height=165,
                label_visibility="collapsed",
            )

            a, b = st.columns(2)
            with a:
                location = st.selectbox(
                    "Target location",
                    ["United Kingdom", "England", "Scotland", "Wales", "Northern Ireland", "London", "Worldwide"],
                )
            with b:
                org_type = st.selectbox(
                    "Organisation type",
                    ["All organisations", "Companies", "Practices / clinics", "Agencies", "Retailers", "Suppliers"],
                )

            c, d = st.columns(2)
            with c:
                industry = st.text_input("Industry", placeholder="e.g. Veterinary")
            with d:
                website = st.text_input("Website (optional)", value=st.session_state.website, placeholder="https://yourwebsite.com")

            if st.button("Find my market →", type="primary", use_container_width=True):
                if not description.strip():
                    st.warning("Please describe your product, service or business first.")
                else:
                    st.session_state.product_description = description
                    st.session_state.selected_location = location
                    st.session_state.website = website
                    nav_to("Analysing")

    with right:
        st.markdown("""
        <div class="surface" style="padding:16px">
          <div class="page-eyebrow">WHAT REACH WILL DO</div>
          <div style="font-size:10px;font-weight:700;margin:8px 0">From an idea to a real addressable market.</div>
          <div style="font-size:7px;color:#718078;line-height:2.2">
            <span class="green">01</span> &nbsp; Understand what you offer<br>
            <span class="green">02</span> &nbsp; Identify relevant industries<br>
            <span class="green">03</span> &nbsp; Define organisation types<br>
            <span class="green">04</span> &nbsp; Find real organisations<br>
            <span class="green">05</span> &nbsp; Build your market workspace
          </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# 03 — AI ANALYSING
# ============================================================

elif st.session_state.page == "Analysing":
    app_topbar()

    st.markdown("""
    <div class="analyse-wrap">
      <div class="analyse-card">
        <div class="analyse-icon">✦</div>
        <h2>Analysing your product...</h2>
        <p>REACH is understanding what you offer and identifying your best-fit market.</p>
        <div class="check-list">
          <div class="check-line"><span class="tick">✓</span> Understanding what you offer</div>
          <div class="check-line"><span class="tick">✓</span> Identifying relevant industries</div>
          <div class="check-line"><span class="tick">✓</span> Analysing market opportunities</div>
          <div class="check-line"><span class="tick">✓</span> Finding potential organisation types</div>
        </div>
        <div class="analyse-track"><i></i></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # This button performs the real analysis; it is intentionally explicit so
    # Streamlit doesn't pretend a background task is running.
    c1, c2, c3 = st.columns([1.25, 1, 1.25])
    with c2:
        if st.button("Run REACH analysis →", type="primary", use_container_width=True):
            with st.spinner("REACH is analysing your market..."):
                # Keep AI analysis and database persistence as two separate steps.
                # This prevents an RLS/database error from being reported as an OpenAI error.
                try:
                    st.session_state.analysis = analyse_product(
                        description=st.session_state.product_description,
                        location=st.session_state.selected_location,
                        website=st.session_state.website,
                    )
                except Exception as e:
                    st.error("REACH couldn't analyse your product.")
                    st.caption("The AI analysis failed before REACH attempted to save anything.")
                    st.code(str(e))
                else:
                    try:
                        save_product_and_strategy(st.session_state.analysis)
                    except Exception as e:
                        st.error("REACH analysed your product, but couldn't save it to your workspace.")
                        st.caption("Your AI result is safe in this session. This is a Supabase/database permission or persistence error, not an OpenAI error.")
                        st.code(str(e))
                    else:
                        nav_to("Market Ready")

# ============================================================
# 04 — MARKET INSIGHTS / READY
# ============================================================

elif st.session_state.page == "Market Ready":
    app_topbar()

    # analyse_product() stores the generated market strategy in `analysis`.
    # Use that real result first; older state names remain as fallbacks.
    strategy = (
        st.session_state.get("analysis")
        or st.session_state.get("strategy")
        or st.session_state.get("market_strategy")
        or {}
    )
    product_description = (
        st.session_state.get("product_description")
        or st.session_state.get("product_input")
        or st.session_state.get("offer_description")
        or ""
    )

    def _strategy_list(*keys):
        for key in keys:
            value = strategy.get(key)
            if isinstance(value, list):
                return [str(x).strip() for x in value if str(x).strip()]
        return []

    def _strategy_text(*keys, default="—"):
        for key in keys:
            value = strategy.get(key)
            if value not in (None, "", []):
                return str(value)
        return default

    customer_segments = _strategy_list(
        "customer_segments", "target_segments", "potential_customers", "segments"
    )
    decision_roles = _strategy_list(
        "decision_makers", "decision_maker_roles", "decision_maker_titles",
        "people_to_reach", "roles"
    )
    discovery_terms = _strategy_list(
        "search_terms", "discovery_searches", "discovery_terms",
        "organisation_search_terms", "organization_search_terms"
    )

    product_name = _strategy_text("product_name", "name", "offer_name", default="")
    if not product_name or product_name.lower() in {"unnamed product", "unknown", "—"}:
        if "veter" in product_description.lower() or any("veter" in x.lower() for x in customer_segments):
            product_name = "Veterinary market"
        else:
            product_name = "Your target market"

    location = _strategy_text("target_location", "location", default="United Kingdom")
    market_results = st.session_state.get("market_results") or []

    st.markdown(
        """
        <style>
        .reach-strategy-hero {
            padding: 24px 26px;
            border: 1px solid rgba(46,234,122,.16);
            border-radius: 16px;
            background:
                radial-gradient(circle at 88% 10%, rgba(46,234,122,.10), transparent 28%),
                linear-gradient(135deg, rgba(7,26,17,.96), rgba(3,14,9,.98));
            margin: 8px 0 18px 0;
        }
        .reach-strategy-kicker {
            color:#2EEA7A;font-size:11px;font-weight:800;letter-spacing:.13em;
        }
        .reach-strategy-title {
            color:#F1F8F4;font-size:30px;font-weight:800;line-height:1.1;margin-top:7px;
        }
        .reach-strategy-copy {
            color:#8EA397;font-size:13px;line-height:1.55;margin-top:8px;max-width:720px;
        }
        .reach-chip {
            display:inline-block;padding:7px 10px;margin:4px 5px 4px 0;
            border-radius:999px;border:1px solid rgba(46,234,122,.17);
            background:rgba(46,234,122,.055);color:#DDF2E6;
            font-size:11px;font-weight:600;
        }
        .reach-card-title {
            color:#F0F8F3;font-size:14px;font-weight:750;margin-bottom:5px;
        }
        .reach-card-sub {
            color:#789084;font-size:11px;line-height:1.45;margin-bottom:12px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="reach-strategy-hero">
            <div class="reach-strategy-kicker">MARKET STRATEGY</div>
            <div class="reach-strategy-title">Your market is ready.</div>
            <div class="reach-strategy-copy">
                REACH has turned your offer into a focused discovery plan. Review who to target,
                who to reach and how REACH will search before building your market.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Strategy", "Ready")
    m2.metric("Target segments", len(customer_segments))
    m3.metric("Decision roles", len(decision_roles))
    m4.metric("Discovery searches", len(discovery_terms))

    st.markdown(f"### {product_name}")
    st.caption(f"Target market: {location}")

    c1, c2, c3 = st.columns(3)

    def _chips(items, empty_text):
        if not items:
            return f'<span style="color:#71857a;font-size:11px">{empty_text}</span>'
        return "".join(f'<span class="reach-chip">{item}</span>' for item in items[:8])

    with c1:
        with st.container(border=True):
            st.markdown('<div class="reach-card-title">Potential customers</div>', unsafe_allow_html=True)
            st.markdown('<div class="reach-card-sub">The organisation types REACH will prioritise.</div>', unsafe_allow_html=True)
            st.markdown(_chips(customer_segments, "No customer segments yet."), unsafe_allow_html=True)
            if len(customer_segments) > 8:
                with st.expander(f"View all {len(customer_segments)}"):
                    for item in customer_segments:
                        st.write(f"• {item}")

    with c2:
        with st.container(border=True):
            st.markdown('<div class="reach-card-title">People to reach</div>', unsafe_allow_html=True)
            st.markdown('<div class="reach-card-sub">Roles likely to influence or make the buying decision.</div>', unsafe_allow_html=True)
            st.markdown(_chips(decision_roles, "No decision-maker roles yet."), unsafe_allow_html=True)
            if len(decision_roles) > 8:
                with st.expander(f"View all {len(decision_roles)}"):
                    for item in decision_roles:
                        st.write(f"• {item}")

    with c3:
        with st.container(border=True):
            st.markdown('<div class="reach-card-title">Discovery searches</div>', unsafe_allow_html=True)
            st.markdown('<div class="reach-card-sub">Searches REACH will use to uncover relevant organisations.</div>', unsafe_allow_html=True)
            st.markdown(_chips(discovery_terms, "No discovery searches yet."), unsafe_allow_html=True)
            if len(discovery_terms) > 8:
                with st.expander(f"View all {len(discovery_terms)}"):
                    for item in discovery_terms:
                        st.write(f"• {item}")

    st.markdown("#### Ready to build?")
    st.caption(
        "REACH will use this strategy to discover organisations. You can review the results before researching people or starting outreach."
    )

    b1, b2 = st.columns([4.5, 1.5])
    with b1:
        if st.button("Build my market →", type="primary", use_container_width=True, key="strategy_build_market"):
            # First recover/reuse anything already saved for this workspace.
            # This prevents repeated Companies House searches and duplicate writes
            # after a browser/server disconnect during a previous build.
            search_terms = discovery_terms or customer_segments
            if not search_terms:
                st.error("REACH needs at least one discovery search before it can build the market.")
            else:
                try:
                    saved = load_saved_companies()
                except Exception:
                    saved = []

                if saved:
                    with st.spinner("REACH is restoring your saved market..."):
                        try:
                            ensure_saved_company_memberships()
                            st.session_state["market_built"] = True
                            st.session_state["company_status_filter"] = "All Companies"
                            nav_to("Companies")
                        except Exception as exc:
                            st.error(f"REACH found your saved companies but could not finish restoring the market links: {exc}")
                else:
                    with st.spinner("REACH is discovering organisations in your market..."):
                        try:
                            discovered = discover_market(search_terms) or []
                            if discovered:
                                save_discovered_companies(discovered)
                                st.session_state["market_built"] = True
                            else:
                                st.session_state["market_results"] = []
                                st.session_state["market_built"] = False
                            st.session_state["company_status_filter"] = "All Companies"
                            nav_to("Companies")
                        except Exception as exc:
                            # Recover saved rows if the browser/server connection failed
                            # after Supabase had already accepted some company writes.
                            try:
                                recovered = load_saved_companies()
                            except Exception:
                                recovered = []
                            if recovered:
                                st.session_state["market_built"] = True
                                st.warning("REACH saved your discovered companies before the connection was interrupted. Opening the saved market instead of running discovery again.")
                                st.session_state["company_status_filter"] = "All Companies"
                                nav_to("Companies")
                            else:
                                st.error(f"REACH could not build the market: {exc}")
    with b2:
        if st.button("Edit strategy", use_container_width=True, key="strategy_edit"):
            nav_to("Enter Product")


elif st.session_state.page == "Companies":
    app_topbar()

    page_header(
        "FIND YOUR MARKET",
        "Companies",
        "Search, filter and work through the organisations REACH has discovered.",
    )

    market = st.session_state.market_results

    # --------------------------------------------------------
    # CLICKABLE TOOLBAR
    # --------------------------------------------------------
    t1, t2, t3, t4, t5, t6, t7 = st.columns([1.05, .8, 1.25, 1.2, .9, 1.0, 1.15])

    with t1:
        view_choice = st.selectbox(
            "View",
            ["Default", "Compact", "Research", "Outreach"],
            index=(["Default", "Compact", "Research", "Outreach"].index(st.session_state.get("company_view_mode", "Default"))
                   if st.session_state.get("company_view_mode", "Default") in ["Default", "Compact", "Research", "Outreach"] else 0),
            label_visibility="collapsed",
            key="company_view_select",
        )
        st.session_state.company_view_mode = view_choice

    with t2:
        if st.button("☰ Filters", use_container_width=True, key="companies_filters"):
            st.session_state.show_company_filters = not st.session_state.get("show_company_filters", False)
            st.rerun()

    with t3:
        if st.button("✦ Research with AI", use_container_width=True, key="companies_ai"):
            nav_to("Research")

    with t4:
        if st.button("⚡ Create workflow", use_container_width=True, key="companies_workflow"):
            nav_to("Workflows")

    with t5:
        if st.button("Save search", use_container_width=True, key="companies_save_search"):
            nav_to("Saved Searches")

    with t6:
        sort_choice = st.selectbox(
            "Sort",
            ["Relevance", "Closest to my location", "Company A–Z", "Company Z–A"],
            label_visibility="collapsed",
            key="company_sort",
        )

    with t7:
        if st.button("⚙ Search settings", use_container_width=True, key="companies_settings"):
            nav_to("Settings")

    # Expandable filter area.
    if st.session_state.get("show_company_filters", False):
        with st.container(border=True):
            st.markdown("#### Filters")
            f1, f2, f3, f4 = st.columns(4)
            with f1:
                location_filter = st.text_input("Location", placeholder="e.g. London", key="company_location_filter")
            with f2:
                min_match = st.slider("Minimum match", 0, 100, 0, key="company_min_match")
            with f3:
                active_only_ui = st.checkbox("Active companies only", value=True, key="company_active_filter")
            with f4:
                source_filter = st.selectbox("Source", ["All sources", "Companies House"], key="company_source_filter")
    else:
        location_filter = ""
        min_match = 0

    query = st.text_input(
        "Search",
        placeholder="Search organisations...",
        label_visibility="collapsed",
        key="company_search_box",
    )

    with st.expander("📍 Location & distance", expanded=(sort_choice == "Closest to my location")):
        lc1, lc2, lc3 = st.columns([1.5, 1, 1])
        with lc1:
            user_location = st.text_input(
                "Your location",
                value=st.session_state.user_location_label,
                placeholder="City or UK postcode, e.g. Ilford or IG2",
                key="user_location_input",
            )
        with lc2:
            radius_choice = st.selectbox(
                "Distance",
                ["Anywhere", "Within 5 miles", "Within 10 miles", "Within 25 miles", "Within 50 miles", "Within 100 miles"],
                key="distance_radius_select",
            )
        with lc3:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Use this location", use_container_width=True, key="apply_user_location"):
                coords = approximate_coords(user_location)
                if coords:
                    st.session_state.user_location_label = user_location
                    st.session_state.user_location_coords = coords
                    st.session_state.distance_radius_miles = radius_choice
                    st.rerun()
                else:
                    st.warning("Try a UK city or postcode such as London, Manchester or IG2.")

        if st.session_state.user_location_coords:
            st.caption(f"Sorting from {st.session_state.user_location_label}. Prototype distances are approximate.")

    filtered = list(market)

    if query:
        q = query.lower()
        filtered = [
            company for company in filtered
            if q in (company_name(company) + " " + company_address(company)).lower()
        ]

    if location_filter:
        lf = location_filter.lower()
        filtered = [c for c in filtered if lf in company_address(c).lower()]

    if min_match:
        filtered = [
            c for c in filtered
            if isinstance(c.get("relevance_score"), (int, float))
            and c.get("relevance_score", 0) >= min_match
        ]

    if sort_choice == "Closest to my location":
        origin = st.session_state.user_location_coords
        if origin:
            for c in filtered:
                c["_distance_miles"] = company_distance(c, origin)
            radius_map = {"Within 5 miles":5,"Within 10 miles":10,"Within 25 miles":25,"Within 50 miles":50,"Within 100 miles":100}
            radius = radius_map.get(st.session_state.distance_radius_miles)
            if radius:
                filtered = [c for c in filtered if c.get("_distance_miles") is not None and c["_distance_miles"] <= radius]
            filtered.sort(key=lambda c: (c.get("_distance_miles") is None, c.get("_distance_miles") or 999999))
        else:
            st.info("Enter a city or UK postcode under Location & distance to sort nearest first.")
    elif sort_choice == "Company A–Z":
        filtered.sort(key=lambda c: company_name(c).lower())
    elif sort_choice == "Company Z–A":
        filtered.sort(key=lambda c: company_name(c).lower(), reverse=True)
    else:
        filtered.sort(key=lambda c: c.get("relevance_score", 0) if isinstance(c.get("relevance_score"), (int,float)) else 0, reverse=True)

    # --------------------------------------------------------
    # CLICKABLE STATUS TABS
    # --------------------------------------------------------
    s1, s2, s3, s4, s5 = st.columns([1.2, 1, 1, 1, 1])
    statuses = ["All companies", "Discovered", "Verified", "Contacted", "Interested"]
    cols = [s1, s2, s3, s4, s5]
    for col, status in zip(cols, statuses):
        with col:
            label = f"{status}  {len(filtered)}" if status == "All companies" else status
            if st.button(
                label,
                use_container_width=True,
                type="primary" if st.session_state.get("company_status_filter", "All companies") == status else "secondary",
                key=f"company_status_{status.lower().replace(' ', '_')}",
            ):
                st.session_state.company_status_filter = status
                st.rerun()

    # Current backend records are discovered until enrichment/outreach backends
    # update their persistent status.
    if st.session_state.get("company_status_filter", "All companies") != "All companies":
        if st.session_state.get("company_status_filter", "All companies") == "Discovered":
            pass
        else:
            filtered = []

    if not market:
        st.info("Build your market first. REACH will show real Companies House results here.")
        if st.button("Go to market strategy →", type="primary"):
            nav_to("Market Ready")
    elif not filtered:
        current_status = st.session_state.get("company_status_filter", "All companies")
        st.info(f"No companies are currently in the {current_status.lower()} stage.")
    else:
        visible = filtered[:st.session_state.market_visible_count]

        # Column headings.
        h = st.columns([.3, 2.2, .85, 1.65, .85, .6, .7, .8])
        for col, label in zip(h, ["", "COMPANY", "STATUS", "LOCATION", "COMPANY NO.", "MATCH", "DISTANCE", "ACTION"]):
            col.markdown(f"<div style='font-size:9px;color:#587064;font-weight:700'>{label}</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)

        for i, company in enumerate(visible):
            name = company_name(company)
            address = company_address(company)
            number = safe(company.get("company_number"))
            score = company.get("relevance_score")
            score_text = f"{score}%" if isinstance(score, (int, float)) and score <= 100 else safe(score)

            row = st.columns([.3, 2.2, .85, 1.65, .85, .6, .7, .8])
            with row[0]:
                st.checkbox("", key=f"select_company_{i}_{number}", label_visibility="collapsed")
            with row[1]:
                if st.button(name, key=f"open_company_{i}_{number}", use_container_width=True):
                    st.session_state.selected_company_index = i
                    st.session_state.selected_company_record = company
                    nav_to("Company Profile")
                st.caption("Source: Companies House")
            with row[2]:
                st.markdown("<span class='tag discovered'>Discovered</span>", unsafe_allow_html=True)
            with row[3]:
                st.markdown(f"<div style='font-size:11px;padding-top:9px'>{address}</div>", unsafe_allow_html=True)
            with row[4]:
                st.markdown(f"<div style='font-size:11px;padding-top:9px'>{number}</div>", unsafe_allow_html=True)
            with row[5]:
                st.markdown(f"<div class='match' style='padding-top:9px'>{score_text}</div>", unsafe_allow_html=True)
            with row[6]:
                distance = company.get("_distance_miles")
                st.markdown(f"<div style='font-size:11px;padding-top:9px'>{f'{distance:.1f} mi' if isinstance(distance,(int,float)) else '—'}</div>", unsafe_allow_html=True)
            with row[7]:
                if st.button("Research", key=f"research_company_{i}_{number}", use_container_width=True):
                    st.session_state.selected_company_record = company
                    nav_to("Research")

            st.markdown("<div style='border-bottom:1px solid rgba(255,255,255,.05);margin:2px 0 6px'></div>", unsafe_allow_html=True)

        if len(visible) < len(filtered):
            if st.button("Load 10 more ↓", use_container_width=True, key="companies_load_more"):
                st.session_state.market_visible_count += 10
                st.rerun()

# ============================================================
# COMPANY PROFILE — clickable organisation record
# ============================================================

elif st.session_state.page == "Company Profile":
    app_topbar()
    company = st.session_state.get("selected_company_record")

    if not company:
        st.warning("Select a company from Companies first.")
        if st.button("← Back to companies"):
            nav_to("Companies")
    else:
        name = company_name(company)
        address = company_address(company)
        number = safe(company.get("company_number"))
        score = company.get("relevance_score")
        score_text = f"{score}%" if isinstance(score, (int, float)) and score <= 100 else safe(score)

        if st.button("← Back to Companies", key="company_profile_back"):
            nav_to("Companies")

        page_header("COMPANY PROFILE", name, "A persistent REACH record for research, people, activity and opportunity history.")

        a, b, c, d = st.columns(4)
        a.metric("Match", score_text)
        b.metric("Status", "Discovered")
        c.metric("Company no.", number)
        d.metric("Source", "Companies House")

        tabs = st.tabs(["Overview", "People", "Research", "Activity", "Emails", "Calls", "Tasks", "Notes", "Opportunities", "Signals"])

        with tabs[0]:
            st.markdown("### Company overview")
            st.write(address)
            st.caption("This profile is based on the current Companies House discovery record. More fields will populate as enrichment providers are connected.")
            x1, x2, x3 = st.columns(3)
            if x1.button("✦ Research with AI", use_container_width=True, key="profile_ai"):
                nav_to("Research")
            if x2.button("♙ Find people", use_container_width=True, key="profile_people"):
                nav_to("People")
            if x3.button("➤ Add to outreach", use_container_width=True, key="profile_outreach"):
                nav_to("Outreach")

        with tabs[1]:
            st.info("No verified people are connected yet. Use Find people to research decision-makers.")
            if st.button("Find decision-makers →", key="profile_find_people"):
                nav_to("People")

        with tabs[2]:
            st.markdown("### Research")
            st.write("Use REACH AI to research this organisation using connected and permitted data sources.")
            if st.button("Start research →", type="primary", key="profile_start_research"):
                nav_to("Research")

        with tabs[3]:
            st.info("Activity history will show discovery, enrichment, outreach, replies, meetings and opportunity changes.")
        with tabs[4]:
            st.info("Email activity will appear after an email integration and approved outreach are connected.")
        with tabs[5]:
            st.info("Call activity will appear after a calling integration is connected.")
        with tabs[6]:
            st.info("No tasks for this organisation yet.")
        with tabs[7]:
            note = st.text_area("Add a note", placeholder="Write a note about this organisation...", key=f"note_{number}")
            st.button("Save note", key=f"save_note_{number}")
        with tabs[8]:
            st.info("No opportunity has been created for this organisation yet.")
            if st.button("Create opportunity →", key="profile_create_opp"):
                nav_to("Pipeline")
        with tabs[9]:
            st.info("Signals will appear when news, hiring, funding or technology data sources are connected.")

# ============================================================
# 06 — PEOPLE SEARCH
# ============================================================

elif st.session_state.page == "People":
    app_topbar()
    page_header("FIND PEOPLE", "Find people", "Identify real professional contacts inside organisations already discovered by REACH.")

    p1,p2,p3,p4,p5,p6 = st.columns([1,.9,1.2,1.2,.9,.9])
    with p1:
        st.selectbox("View", ["Default","Compact","Research","Outreach"], label_visibility="collapsed", key="people_view")
    with p2:
        if st.button("☰ Filters", use_container_width=True, key="people_filters"):
            st.session_state.people_filter_open = not st.session_state.people_filter_open
            st.rerun()
    with p3:
        if st.button("✦ Research with AI", use_container_width=True, key="people_ai"):
            nav_to("Research")
    with p4:
        if st.button("⚡ Create workflow", use_container_width=True, key="people_workflow"):
            nav_to("Workflows")
    with p5:
        if st.button("Save search", use_container_width=True, key="people_save"):
            nav_to("Saved Searches")
    with p6:
        if st.button("⚙ Settings", use_container_width=True, key="people_settings"):
            nav_to("Settings")

    st.text_input(
        "People search",
        placeholder="Filter returned contacts by name, job title or company...",
        label_visibility="collapsed",
        key="people_search"
    )

    if st.session_state.people_filter_open:
        with st.container(border=True):
            f1,f2,f3,f4 = st.columns(4)
            with f1:
                st.multiselect("Job titles", ["Founder","Owner","Director","Manager","Head of","Partner","Operations"], key="people_titles")
            with f2:
                st.multiselect("Seniority", ["Owner","C-Suite","VP","Director","Manager"], key="people_seniority")
            with f3:
                st.text_input("Location", placeholder="e.g. London", key="people_location")
            with f4:
                st.selectbox("Contact availability", ["Any","Verified email","Phone","Both"], key="people_contact")
            g1,g2,g3,g4 = st.columns(4)
            with g1:
                st.text_input("Company", placeholder="Company name", key="people_company")
            with g2:
                st.selectbox("Market status", ["Any","Discovered","Verified","Contacted","Interested"], key="people_market_status")
            with g3:
                st.slider("Minimum REACH match", 0, 100, 0, key="people_match")
            with g4:
                st.selectbox("Sort", ["Relevance","Name A–Z","Company A–Z"], key="people_sort")

    # Explicit search button: Hunter Domain Search consumes credits, so REACH
    # does not automatically call it every time Streamlit reruns.
    s1, s2 = st.columns([1.4, 4.6])
    with s1:
        search_people = st.button(
            "Find people →",
            type="primary",
            use_container_width=True,
            key="hunter_find_people"
        )
    with s2:
        if not hunter_is_configured():
            st.warning("Hunter is not connected. Add HUNTER_API_KEY to .env and restart REACH.")
        elif not st.session_state.market_results:
            st.info("Build your market first so REACH has organisations to search.")
        else:
            st.caption(
                f"Ready to search the first {min(5, len(st.session_state.market_results))} discovered organisations. "
                "REACH only searches when you click the button so API credits are not used accidentally."
            )

    if search_people:
        if not hunter_is_configured():
            st.error("Hunter API key was not loaded. Save .env, stop Streamlit with Ctrl+C, then run it again.")
        elif not st.session_state.market_results:
            st.error("No companies are available yet. Build your market first.")
        else:
            with st.spinner("Finding sample professional contacts..."):
                found, errors = find_people_for_companies(
                    st.session_state.market_results,
                    max_companies=5,
                    per_company=10,
                )
            st.session_state.people_results = found
            st.session_state.people_search_errors = errors
            st.session_state.people_has_searched = True
            st.rerun()

    people = list(st.session_state.people_results)

    # Apply the on-page filters to the real returned records.
    q = (st.session_state.get("people_search") or "").strip().lower()
    company_q = (st.session_state.get("people_company") or "").strip().lower()
    title_filters = [x.lower() for x in st.session_state.get("people_titles", [])]
    seniority_filters = [x.lower() for x in st.session_state.get("people_seniority", [])]
    availability = st.session_state.get("people_contact", "Any")

    def _person_matches(person):
        haystack = " ".join([
            str(person.get("name", "")),
            str(person.get("job_title", "")),
            str(person.get("company", "")),
            str(person.get("department", "")),
        ]).lower()
        if q and q not in haystack:
            return False
        if company_q and company_q not in str(person.get("company", "")).lower():
            return False
        title = str(person.get("job_title", "")).lower()
        if title_filters and not any(t in title for t in title_filters):
            return False
        seniority = str(person.get("seniority", "")).lower()
        if seniority_filters and not any(s in seniority for s in seniority_filters):
            return False
        has_email = person.get("email") not in (None, "", "—")
        has_phone = person.get("phone") not in (None, "", "—")
        verified = str(person.get("verification_status", "")).lower() in {"valid", "verified"}
        if availability == "Verified email" and not (has_email and verified):
            return False
        if availability == "Phone" and not has_phone:
            return False
        if availability == "Both" and not (has_email and has_phone):
            return False
        return True

    filtered_people = [p for p in people if _person_matches(p)]

    sort_mode = st.session_state.get("people_sort", "Relevance")
    if sort_mode == "Name A–Z":
        filtered_people.sort(key=lambda p: str(p.get("name", "")).lower())
    elif sort_mode == "Company A–Z":
        filtered_people.sort(key=lambda p: str(p.get("company", "")).lower())

    total_count = len(filtered_people)
    t1,t2,t3 = st.columns(3)
    counts = {"Total": total_count, "Net New": total_count, "Saved": 0}
    for col,label in zip([t1,t2,t3], ["Total","Net New","Saved"]):
        with col:
            if st.button(
                f"{label}  {counts[label]}",
                use_container_width=True,
                type="primary" if st.session_state.people_status == label else "secondary",
                key=f"people_tab_{label}"
            ):
                st.session_state.people_status = label
                st.rerun()

    if filtered_people:
        display_rows = []
        for p in filtered_people:
            confidence = p.get("confidence")
            display_rows.append({
                "Name": safe(p.get("name")),
                "Job title": safe(p.get("job_title")),
                "Seniority": safe(p.get("seniority")),
                "Company": safe(p.get("company")),
                "Email": safe(p.get("email")),
                "Verification": safe(p.get("verification_status")),
                "Confidence": f"{confidence}%" if isinstance(confidence, (int, float)) else "—",
                "Department": safe(p.get("department")),
                "Source": "Hunter",
            })
        st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)
        st.caption("These contacts were returned by Hunter. REACH does not invent names, emails or verification statuses.")
    elif st.session_state.people_has_searched:
        st.info("Hunter did not return contacts matching these filters. Try clearing filters or searching more organisations.")
    else:
        st.info("Click “Find people with Hunter” to search your discovered organisations for real professional contacts.")

    if st.session_state.people_search_errors:
        with st.expander("Some organisations could not be searched"):
            for err in st.session_state.people_search_errors[:10]:
                st.write(f"• {err}")

    a1,a2,a3 = st.columns(3)
    if a1.button("Research companies →", use_container_width=True, key="people_companies"):
        nav_to("Companies")
    if a2.button("Configure enrichment →", use_container_width=True, key="people_enrichment"):
        nav_to("Enrichment")
    if a3.button("Manage personas →", use_container_width=True, key="people_personas"):
        nav_to("Personas")

# ============================================================
# 07 — OUTREACH
# ============================================================

elif st.session_state.page == "Outreach":
    app_topbar()
    page_header("REACH YOUR MARKET", "Create your campaign", "Build, review and control a personalised outreach workflow.")

    o1,o2,o3,o4 = st.columns(4)
    if o1.button("＋ New sequence", type="primary", use_container_width=True, key="out_new"):
        st.session_state.outreach_step = "Personalised email"
    if o2.button("Templates", use_container_width=True, key="out_templates"):
        nav_to("Templates")
    if o3.button("Workflows", use_container_width=True, key="out_workflows"):
        nav_to("Workflows")
    if o4.button("Email setup", use_container_width=True, key="out_email_setup"):
        nav_to("Integrations")

    st.markdown("### Campaign sequence")
    steps = [("Day 1","Personalised email"),("Day 4","Follow-up"),("Day 8","Second follow-up"),
             ("Reply","Stop automatically"),("Positive","Move to opportunity")]
    for day,label in steps:
        c1,c2,c3 = st.columns([.8,4,.9])
        c1.caption(day)
        if c2.button(label, use_container_width=True, key=f"out_step_{label}"):
            st.session_state.outreach_step = label
            st.rerun()
        c3.caption("Selected" if st.session_state.outreach_step == label else "")

    with st.container(border=True):
        st.markdown(f"#### {st.session_state.outreach_step}")
        if "email" in st.session_state.outreach_step.lower() or "follow" in st.session_state.outreach_step.lower():
            st.text_input("Subject", placeholder="Personalised subject line", key="out_subject")
            st.text_area("Message", placeholder="Write or generate the message...", height=130, key="out_message")
            b1,b2,b3 = st.columns(3)
            if b1.button("✦ Generate draft", use_container_width=True, key="out_generate"):
                st.session_state["draft_generated"] = True
            if b2.button("Save step", use_container_width=True, key="out_save"):
                st.success("Step saved in this session.")
            if b3.button("Preview", use_container_width=True, key="out_preview"):
                st.session_state["show_preview"] = True
        else:
            st.write("This rule controls what REACH should do when this event occurs.")

    st.warning("Connect email and approve campaign rules before sending.")

# ============================================================
# 08 — ANALYTICS / FULL PIPELINE
# ============================================================

elif st.session_state.page == "Analytics":
    app_topbar()
    total = market_total()

    page_header(
        "ANALYTICS",
        "Market pipeline",
        "See how much of your market REACH has discovered, researched, contacted and converted.",
    )

    st.markdown(
        f"""
        <div class="pipeline">
          <div class="pipeline-card"><b>{total}</b><span>⚪ Discovered</span></div>
          <div class="pipeline-card"><b style="color:#43a9ff">0</b><span>🔵 Verified</span></div>
          <div class="pipeline-card"><b style="color:#f4c84d">0</b><span>🟡 Contacted</span></div>
          <div class="pipeline-card"><b style="color:#2df58a">0</b><span>🟢 Interested</span></div>
        </div>

        <div class="surface chart">
          <div class="chart-head"><b>Progress over time</b><span>Market coverage</span></div>
          <div class="bars">
            <div class="bar" style="height:18%"></div>
            <div class="bar" style="height:27%"></div>
            <div class="bar" style="height:34%"></div>
            <div class="bar" style="height:46%"></div>
            <div class="bar" style="height:55%"></div>
            <div class="bar" style="height:66%"></div>
            <div class="bar" style="height:78%"></div>
            <div class="bar" style="height:91%"></div>
          </div>
          <div class="bar-labels"><span>1</span><span>2</span><span>3</span><span>4</span><span>5</span><span>6</span><span>7</span><span>8</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption("The chart is a visual product-state preview until historical campaign data is connected.")

# ============================================================
# OPPORTUNITIES
# ============================================================

elif st.session_state.page == "Opportunities":
    app_topbar()
    page_header(
        "OPPORTUNITIES",
        "Turn opportunities green",
        "Interested organisations, meetings and customers will be managed here.",
    )

    st.html("""
    <div class="metrics4">
      <div class="metricbox green"><b>0</b><span>Interested</span></div>
      <div class="metricbox green"><b>0</b><span>Meetings booked</span></div>
      <div class="metricbox green"><b>0</b><span>Customers</span></div>
      <div class="metricbox"><b>—</b><span>Conversion rate</span></div>
    </div>
    <div class="surface" style="padding:20px;text-align:center;margin-top:10px">
      <div style="font-size:11px;font-weight:700">No opportunities yet</div>
      <div style="font-size:7px;color:#69786f;margin-top:5px">Interested replies will appear here automatically once outreach is connected.</div>
    </div>
    """)

# ============================================================
# AI / RESEARCH / AUTOMATIONS
# ============================================================

elif st.session_state.page == "AI":
    app_topbar()
    page_header(
        "REACH AI",
        "Ask REACH AI",
        "Research your market, draft outreach and turn questions into practical next steps."
    )

    if "reach_ai_messages" not in st.session_state:
        st.session_state.reach_ai_messages = []

    # Show a few useful one-click prompts.
    q1, q2, q3, q4 = st.columns(4)
    quick_prompt = None
    if q1.button("Draft outreach", use_container_width=True, key="ai_quick_outreach"):
        quick_prompt = "Draft a concise personalised outreach email for my target market."
    if q2.button("Who should I target?", use_container_width=True, key="ai_quick_target"):
        quick_prompt = "Based on my current market strategy, who should I target and why?"
    if q3.button("Improve my approach", use_container_width=True, key="ai_quick_improve"):
        quick_prompt = "Review my current market approach and suggest practical improvements."
    if q4.button("Next best action", use_container_width=True, key="ai_quick_next"):
        quick_prompt = "What should my next best action be in REACH based on my current progress?"

    # Existing REACH context is supplied to the assistant so users do not have
    # to repeatedly explain their product and market.
    analysis = st.session_state.get("analysis") or {}
    product_description = st.session_state.get("product_description") or ""
    selected_company = st.session_state.get("selected_company_record")
    company_context = ""
    if selected_company:
        try:
            company_context = company_name(selected_company)
        except Exception:
            company_context = str(selected_company)

    user_prompt = st.text_area(
        "Ask REACH AI",
        value=quick_prompt or "",
        placeholder="e.g. Write a first outreach email for a veterinary practice...",
        height=115,
        label_visibility="collapsed",
        key="reach_ai_prompt"
    )

    ask = st.button("✦ Ask REACH AI →", type="primary", key="reach_ai_submit")

    if ask and user_prompt.strip():
        # Portfolio demo: generate a deterministic local preview instead of
        # calling OpenAI. This cannot consume API credits.
        target_roles = (analysis.get("decision_makers") or [])[:3]
        segments = (analysis.get("customer_segments") or [])[:3]
        selected_text = company_context or "a selected organisation"
        if "outreach" in user_prompt.lower() or "email" in user_prompt.lower():
            answer = (
                "Demo response: A strong first message would briefly explain the problem you solve, "
                f"connect it to {selected_text}, and ask for a short conversation rather than making a hard sell. "
                "In the production version, REACH AI can draft this using verified organisation context."
            )
        elif "target" in user_prompt.lower():
            answer = (
                "Demo response: Prioritise the customer segments shown in your Market Strategy"
                + (f" — {', '.join(segments)}" if segments else "")
                + (f". Relevant decision-maker roles include {', '.join(target_roles)}." if target_roles else ".")
            )
        else:
            answer = (
                "Demo response: Your next step is to review the discovered organisations, research fit, "
                "identify the appropriate decision-maker roles, and only then prepare outreach. "
                "This portfolio environment uses sample data and does not call external AI services."
            )
        st.session_state.reach_ai_messages.append(
            {"role": "user", "content": user_prompt.strip()}
        )
        st.session_state.reach_ai_messages.append(
            {"role": "assistant", "content": answer}
        )
        st.rerun()

    if st.session_state.reach_ai_messages:
        st.markdown("### Conversation")
        for message in st.session_state.reach_ai_messages:
            role = message.get("role", "assistant")
            with st.chat_message(role):
                st.markdown(message.get("content", ""))

        if st.button("Clear conversation", key="reach_ai_clear"):
            st.session_state.reach_ai_messages = []
            st.rerun()
    else:
        st.caption(
            "REACH AI uses your current product and market context automatically. "
            "It will not invent contact details or pretend unverified research is real."
        )

elif st.session_state.page == "Research":
    app_topbar()
    page_header(
        "RESEARCH & ENRICHMENT",
        "Research organisations",
        "Check organisation fit, decision-makers and contact routes before outreach."
    )

    selected = st.session_state.get("selected_company_record")
    if selected:
        st.success(f"Selected: {company_name(selected)}")

    r1, r2, r3 = st.columns(3)
    with r1:
        st.selectbox(
            "Research",
            ["Selected organisation", "All discovered organisations", "Saved companies"],
            key="research_target"
        )
    with r2:
        st.selectbox(
            "Depth",
            ["Quick verification", "Standard research", "Deep research"],
            key="research_depth"
        )
    with r3:
        st.selectbox(
            "Focus",
            ["Organisation fit", "Decision-makers", "Contact routes", "Signals", "All"],
            key="research_focus"
        )

    st.text_area(
        "Research instructions",
        placeholder="Optional: tell REACH what else to look for...",
        height=90,
        key="research_instructions"
    )

    c1, c2, c3 = st.columns(3)
    if c1.button("✦ Start research", type="primary", use_container_width=True, key="research_start"):
        st.session_state["research_started"] = True
        st.session_state["research_stage"] = 5
        st.rerun()
    if c2.button("Open companies", use_container_width=True, key="research_companies"):
        nav_to("Companies")
    if c3.button("Configure enrichment", use_container_width=True, key="research_enrich"):
        nav_to("Enrichment")

    if st.session_state.get("research_started"):
        st.markdown("### Research progress")

        stages = [
            ("✓", "Organisation verified", "Company record checked"),
            ("✓", "Website checked", "Public website research prepared"),
            ("✓", "Fit assessed", "Matched against your market strategy"),
            ("✓", "Decision-makers", "Relevant roles identified for enrichment"),
            ("✓", "Contact routes", "Available routes prepared for verification"),
        ]

        cols = st.columns(5)
        for col, (icon, title, detail) in zip(cols, stages):
            with col:
                st.markdown(
                    f"""
                    <div style="
                        min-height:112px;
                        padding:14px;
                        border:1px solid rgba(46,234,122,.18);
                        border-radius:10px;
                        background:rgba(4,20,13,.88);
                    ">
                        <div style="font-size:17px;color:#2EEA7A;font-weight:800">{icon}</div>
                        <div style="font-size:12px;color:#edf8f1;font-weight:750;margin-top:7px">{title}</div>
                        <div style="font-size:10.5px;color:#82978b;line-height:1.45;margin-top:5px">{detail}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("### Research summary")

        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Organisation", "Verified")
        q2.metric("Market fit", "Ready to assess")
        q3.metric("People", "Needs enrichment")
        q4.metric("Contact routes", "Needs verification")

        with st.container(border=True):
            st.markdown("#### What REACH knows")
            if selected:
                st.write(f"**Organisation:** {company_name(selected)}")
                st.write(f"**Address:** {company_address(selected)}")
                st.write(f"**Company number:** {safe(selected.get('company_number'))}")
                score = selected.get("relevance_score")
                if isinstance(score, (int, float)):
                    st.write(f"**Discovery match:** {score}%")
            else:
                st.write("Choose an organisation from Companies to see its verified discovery details here.")

            st.caption(
                "REACH will add website findings, verified people and contact details here "
                "when the corresponding permitted data providers are connected."
            )

        n1, n2, n3 = st.columns(3)
        if n1.button("Find decision-makers →", use_container_width=True, key="research_find_people"):
            nav_to("People")
        if n2.button("Add to outreach →", use_container_width=True, key="research_add_outreach"):
            nav_to("Outreach")
        if n3.button("View company profile →", use_container_width=True, key="research_profile"):
            nav_to("Company Profile")

elif st.session_state.page == "Automations":
    app_topbar()
    page_header("AUTOMATIONS", "Automate the market workflow", "Create rules that move organisations through REACH.")
    st.html("""
    <div class="surface" style="padding:17px;margin-top:12px">
      <div style="font-size:9px;font-weight:700">Discovered → Verify → Research → Contact → Classify reply → Update status</div>
      <div style="font-size:7px;color:#68776e;margin-top:6px">The automation backend will connect these stages while preserving campaign controls and stop rules.</div>
    </div>
    """)



# ============================================================
# REACH-SPECIFIC DEEP WORKSPACES
# ============================================================

elif st.session_state.page == "Market Coverage":
    app_topbar()
    total = market_total()
    page_header("PROSPECT & ENRICH", "Market coverage", "See how much of your defined market REACH has identified and what remains unreached.")

    st.html(f"""
    <div class="coverage-grid">
      <section class="surface" style="padding:20px">
        <div class="home-card-head"><h3>Coverage overview</h3><span style="font-size:10px;color:#2df58a">LIVE WORKSPACE</span></div>
        <div class="coverage-ring"><div><b>{'38%' if total else '0%'}</b><span>market coverage</span></div></div>
        <div class="metrics4">
          <div class="metricbox"><b>{total}</b><span>Identified</span></div>
          <div class="metricbox blue"><b>0</b><span>Verified</span></div>
          <div class="metricbox yellow"><b>0</b><span>Reached</span></div>
          <div class="metricbox green"><b>0</b><span>Opportunities</span></div>
        </div>
      </section>
      <section class="surface" style="padding:20px">
        <div class="home-card-head"><h3>Coverage gaps</h3><span style="font-size:10px;color:#7f8e85">Next best areas</span></div>
        <div class="signal-row"><div class="act-icon">1</div><div><b>Unreached organisations</b><span>Prioritise discovered organisations with no outreach history.</span></div><span>High impact</span><span class="green">→</span></div>
        <div class="signal-row"><div class="act-icon">2</div><div><b>Missing decision-makers</b><span>Research companies where no suitable contact is verified.</span></div><span>Research</span><span class="green">→</span></div>
        <div class="signal-row"><div class="act-icon">3</div><div><b>Adjacent segments</b><span>Expand after conversion evidence identifies strong segments.</span></div><span>Later</span><span class="green">→</span></div>
      </section>
    </div>
    <section class="surface" style="padding:20px;margin-top:12px">
      <div class="home-card-head"><h3>Coverage by segment</h3><span style="font-size:10px;color:#7f8e85">Illustrative until segment history is stored</span></div>
      <div class="segment-row head"><span>Segment</span><span>Identified</span><span>Coverage</span><span>Action</span></div>
      <div class="segment-row"><b>Primary target segment</b><span>{total}</span><div class="seg-track"><i style="width:{'38%' if total else '0%'}"></i></div><span class="green">View →</span></div>
      <div class="segment-row"><b>Adjacent segment</b><span>—</span><div class="seg-track"><i style="width:0%"></i></div><span>Explore</span></div>
      <div class="segment-row"><b>Expansion market</b><span>—</span><div class="seg-track"><i style="width:0%"></i></div><span>Explore</span></div>
    </section>
    """)

elif st.session_state.page == "Market Map":
    app_topbar()
    page_header("PROSPECT & ENRICH", "Market map", "Explore your market by geography, segment and organisation status.")
    st.html("""
    <div class="workspace-tabs"><span class="workspace-tab on">Geography</span><span class="workspace-tab">Segments</span><span class="workspace-tab">Status</span><span class="workspace-tab">Opportunities</span></div>
    <div class="coverage-grid">
      <section class="surface" style="min-height:430px;padding:20px;position:relative;overflow:hidden">
        <div class="home-card-head"><h3>United Kingdom market</h3><span style="font-size:10px;color:#2df58a">REACH MAP</span></div>
        <div style="position:absolute;inset:70px 35px 35px;background:radial-gradient(circle at 42% 30%,rgba(45,245,138,.18),transparent 6%),radial-gradient(circle at 56% 46%,rgba(45,245,138,.14),transparent 5%),radial-gradient(circle at 47% 67%,rgba(45,245,138,.15),transparent 5%),radial-gradient(circle at 68% 61%,rgba(45,245,138,.10),transparent 4%),linear-gradient(145deg,#07170f,#03100a);border:1px solid rgba(45,245,138,.12);border-radius:12px">
          <div style="position:absolute;left:41%;top:29%;width:10px;height:10px;background:#2df58a;border-radius:50%;box-shadow:0 0 18px #2df58a"></div>
          <div style="position:absolute;left:55%;top:45%;width:8px;height:8px;background:#43a9ff;border-radius:50%"></div>
          <div style="position:absolute;left:46%;top:66%;width:9px;height:9px;background:#f4c84d;border-radius:50%"></div>
          <div style="position:absolute;left:67%;top:60%;width:8px;height:8px;background:#2df58a;border-radius:50%"></div>
        </div>
      </section>
      <section class="surface" style="padding:20px">
        <h3 style="font-size:15px">Map legend</h3>
        <div class="pipe-line"><span>⚪ Discovered</span><b>Organisation found</b></div>
        <div class="pipe-line"><span>🔵 Verified</span><b>Contact route found</b></div>
        <div class="pipe-line"><span>🟡 Contacted</span><b>Outreach sent</b></div>
        <div class="pipe-line"><span>🟢 Interested</span><b>Opportunity</b></div>
        <div style="margin-top:18px;font-size:11px;color:#7d8b82;line-height:1.6">A live geographic map can be connected once postcode/geocoding data is added to the market database.</div>
      </section>
    </div>
    """)

elif st.session_state.page == "Market Memory":
    app_topbar()
    page_header("PROSPECT & ENRICH", "Market memory", "REACH remembers what it learned about every organisation, interaction and outcome.")
    st.html("""
    <div class="filter-grid">
      <div class="memory-card"><b>Organisation memory</b><p>Why each organisation matched, its status and research history.</p></div>
      <div class="memory-card"><b>Contact memory</b><p>Decision-makers, verified routes and previous interactions.</p></div>
      <div class="memory-card"><b>Message memory</b><p>Which positioning and outreach was used for each segment.</p></div>
      <div class="memory-card"><b>Outcome memory</b><p>Replies, objections, interest, meetings and customer outcomes.</p></div>
    </div>
    <div class="coverage-grid">
      <section class="surface" style="padding:20px">
        <div class="home-card-head"><h3>Learning timeline</h3><span style="font-size:10px;color:#2df58a">Persistent context</span></div>
        <div class="timeline">
          <div class="timeline-item"><b>Market defined</b><p>REACH stores your target segments, decision-maker roles and discovery logic.</p></div>
          <div class="timeline-item"><b>Organisations discovered</b><p>Every discovered organisation is deduplicated and given a persistent market record.</p></div>
          <div class="timeline-item"><b>Research added</b><p>Company fit, people and verified contact routes become part of the record.</p></div>
          <div class="timeline-item"><b>Outcomes learned</b><p>Responses and conversions can later improve prioritisation and expansion suggestions.</p></div>
        </div>
      </section>
      <section class="surface" style="padding:20px">
        <h3 style="font-size:15px">What REACH should learn</h3>
        <div class="pipe-line"><span>Best converting segment</span><b>Waiting for data</b></div>
        <div class="pipe-line"><span>Best decision-maker role</span><b>Waiting for data</b></div>
        <div class="pipe-line"><span>Best message angle</span><b>Waiting for data</b></div>
        <div class="pipe-line"><span>Best region</span><b>Waiting for data</b></div>
      </section>
    </div>
    """)

elif st.session_state.page == "Signals":
    app_topbar()
    page_header("RESEARCH & ENRICHMENT", "Signals", "Use timely business signals to prioritise companies and make outreach more relevant.")
    st.html("""
    <div class="workspace-tabs"><span class="workspace-tab on">All signals</span><span class="workspace-tab">Growth</span><span class="workspace-tab">Hiring</span><span class="workspace-tab">Funding</span><span class="workspace-tab">News</span><span class="workspace-tab">Technology</span></div>
    <section class="surface" style="padding:20px">
      <div class="signal-row"><div class="act-icon">⚡</div><div><b>Signals will appear here</b><span>Connect permitted company/news data sources to surface meaningful buying or growth signals.</span></div><span>Data source required</span><span class="green">Connect →</span></div>
      <div class="signal-row"><div class="act-icon">✦</div><div><b>REACH AI prioritisation</b><span>Signals can later be combined with market fit and interaction history.</span></div><span>Planned</span><span>—</span></div>
    </section>
    """)

elif st.session_state.page == "Integrations":
    app_topbar()
    page_header("PLATFORM", "Integrations", "Connect the systems REACH needs for research, outreach, calendars and CRM workflows.")
    st.html("""
    <div class="workspace-tabs"><span class="workspace-tab on">All</span><span class="workspace-tab">Email</span><span class="workspace-tab">CRM</span><span class="workspace-tab">Calendar</span><span class="workspace-tab">Data</span></div>
    <div class="integration-grid">
      <div class="integration"><b>Google / Gmail</b><p>Email sending, replies and inbox activity.</p><span class="connect-pill">Connect</span></div>
      <div class="integration"><b>Microsoft 365</b><p>Outlook email and calendar workflows.</p><span class="connect-pill">Connect</span></div>
      <div class="integration"><b>HubSpot</b><p>Sync companies, contacts and opportunity stages.</p><span class="connect-pill">Connect</span></div>
      <div class="integration"><b>Salesforce</b><p>CRM records, activities and pipeline sync.</p><span class="connect-pill">Connect</span></div>
      <div class="integration"><b>Calendar</b><p>Meeting availability and booked meeting tracking.</p><span class="connect-pill">Connect</span></div>
      <div class="integration"><b>Companies House</b><p>UK company discovery source used by the current REACH prototype.</p><span class="connect-pill">Configured in .env</span></div>
      <div class="integration"><b>Business data provider</b><p>Future enrichment for websites, people and verified business contact routes.</p><span class="connect-pill">Add provider</span></div>
      <div class="integration"><b>Webhook / API</b><p>Send REACH events to your own systems and workflows.</p><span class="connect-pill">Configure</span></div>
      <div class="integration"><b>CSV import</b><p>Bring an existing organisation list into a REACH market.</p><span class="connect-pill">Import</span></div>
    </div>
    """)

elif st.session_state.page == "Data Quality":
    app_topbar()
    page_header("PLATFORM", "Data quality", "See where market records are complete, duplicated, stale or still need verification.")
    total = market_total()
    st.html(f"""
    <div class="metrics4">
      <div class="metricbox"><b>{total}</b><span>Total organisation records</span></div>
      <div class="metricbox blue"><b>0</b><span>Verified contact routes</span></div>
      <div class="metricbox yellow"><b>0</b><span>Needs review</span></div>
      <div class="metricbox green"><b>0</b><span>Suppressed</span></div>
    </div>
    <section class="surface" style="padding:20px;margin-top:12px">
      <div class="health-row head"><span>Check</span><span>Status</span><span>Records</span><span>Action</span></div>
      <div class="health-row"><b>Organisation deduplication</b><span class="green">Active</span><span>{total}</span><span>Review →</span></div>
      <div class="health-row"><b>Company status</b><span class="green">Active filter</span><span>{total}</span><span>Review →</span></div>
      <div class="health-row"><b>Website verification</b><span>Not connected</span><span>0</span><span class="green">Connect →</span></div>
      <div class="health-row"><b>Contact verification</b><span>Not connected</span><span>0</span><span class="green">Connect →</span></div>
      <div class="health-row"><b>Suppression / opt-out</b><span>Ready</span><span>0</span><span>View →</span></div>
    </section>
    """)

elif st.session_state.page == "Suppression List":
    app_topbar()
    page_header("PLATFORM", "Suppression list", "Keep opted-out or do-not-contact people and organisations out of future outreach.")
    st.html("""
    <div class="surface" style="padding:20px;margin-top:14px">
      <div class="home-card-head"><h3>Suppressed records</h3><span style="font-size:10px;color:#7f8e85">0 records</span></div>
      <div class="people-empty"><b>No suppressed records yet</b>Opt-outs and manual do-not-contact records will be stored here and excluded from outreach.</div>
    </div>
    """)

elif st.session_state.page == "Notifications":
    app_topbar()
    page_header("PLATFORM", "Notifications", "Choose which market, outreach and opportunity events should get your attention.")
    st.html("""
    <section class="surface" style="padding:20px;margin-top:14px">
      <div class="health-row head"><span>Notification</span><span>Channel</span><span>Status</span><span>Control</span></div>
      <div class="health-row"><b>Interested reply</b><span>In app</span><span class="green">On</span><span>Configure</span></div>
      <div class="health-row"><b>Meeting booked</b><span>In app</span><span class="green">On</span><span>Configure</span></div>
      <div class="health-row"><b>Campaign needs attention</b><span>In app</span><span class="green">On</span><span>Configure</span></div>
      <div class="health-row"><b>Market coverage milestone</b><span>In app</span><span>On</span><span>Configure</span></div>
    </section>
    """)


# ============================================================
# APOLLO-DEPTH PROSPECTING / RECORD MANAGEMENT
# ============================================================

elif st.session_state.page in ["Saved People", "Saved Companies"]:
    app_topbar()
    kind = "people" if st.session_state.page == "Saved People" else "companies"
    page_header("PROSPECT & ENRICH", st.session_state.page, f"Manage saved {kind}, enrichment, activity and next actions from one workspace.")
    st.html(f"""
    <div class="workspace-tabs"><span class="workspace-tab on">All saved</span><span class="workspace-tab">Needs enrichment</span><span class="workspace-tab">Recently active</span><span class="workspace-tab">By stage</span></div>
    <div class="bulkbar"><span class="bulk green">✦ Research with AI</span><span class="bulk">Enrich</span><span class="bulk">Add to list</span><span class="bulk">Add to sequence</span><span class="bulk">Create workflow</span><span class="bulk">Export</span><span class="bulk">Edit fields</span></div>
    <div class="surface" style="padding:18px">
      <div class="home-card-head"><h3>Saved {kind}</h3><span style="font-size:10px;color:#7f8e85">0 saved</span></div>
      <div class="people-empty"><b>No saved {kind} yet</b>Save records from search to manage enrichment, activity, recommendations and outreach here.</div>
    </div>
    """)

elif st.session_state.page == "Personas":
    app_topbar()
    page_header("PROSPECT & ENRICH", "Personas", "Define reusable decision-maker profiles for prospecting, research and outreach.")
    st.html("""
    <div class="saved-grid">
      <div class="saved-card"><span class="alert">REACH PERSONA</span><h3 style="font-size:15px">Primary decision-maker</h3><p>Job-title, seniority, department, location and company-fit rules can be saved here.</p><span class="green" style="font-size:10px">Create persona →</span></div>
      <div class="saved-card"><b>Influencer persona</b><p>Define people who influence the buying decision but may not own budget.</p><span class="green" style="font-size:10px">Create persona →</span></div>
      <div class="saved-card"><b>Exclude persona</b><p>Prevent irrelevant roles from entering research and outreach workflows.</p><span class="green" style="font-size:10px">Create exclusion →</span></div>
    </div>
    """)

elif st.session_state.page == "Scores":
    app_topbar()
    page_header("PROSPECT & ENRICH", "Scores", "Create fit and priority scores using market, organisation and engagement signals.")
    st.html("""
    <div class="metrics4"><div class="metricbox green"><b>A</b><span>High fit</span></div><div class="metricbox blue"><b>B</b><span>Good fit</span></div><div class="metricbox yellow"><b>C</b><span>Review</span></div><div class="metricbox"><b>D</b><span>Low priority</span></div></div>
    <div class="surface" style="padding:20px;margin-top:12px">
      <div class="health-row head"><span>Scoring rule</span><span>Weight</span><span>Status</span><span>Action</span></div>
      <div class="health-row"><b>Target segment match</b><span>High</span><span class="green">Active</span><span>Edit</span></div>
      <div class="health-row"><b>Location match</b><span>Medium</span><span class="green">Active</span><span>Edit</span></div>
      <div class="health-row"><b>Decision-maker found</b><span>High</span><span>Waiting</span><span>Edit</span></div>
      <div class="health-row"><b>Engagement signal</b><span>High</span><span>Waiting</span><span>Edit</span></div>
    </div>
    """)

elif st.session_state.page == "Territories":
    app_topbar()
    page_header("PROSPECT & ENRICH", "Territories", "Organise markets by geography, segment, owner or business rules.")
    st.html("""
    <div class="saved-grid">
      <div class="saved-card"><b>United Kingdom</b><p>Primary territory based on the current REACH market.</p><span class="alert">ACTIVE</span></div>
      <div class="saved-card"><b>New territory</b><p>Create a geography or segment-based territory and assign market rules.</p><span class="green" style="font-size:10px">Create →</span></div>
      <div class="saved-card"><b>Expansion territory</b><p>Use conversion evidence to decide where REACH should expand next.</p><span class="green" style="font-size:10px">Explore →</span></div>
    </div>
    """)

elif st.session_state.page == "Workflows":
    app_topbar()
    page_header("ENGAGE", "Workflows", "Automate REACH using a trigger, optional conditions and one or more actions.")
    w1,w2,w3 = st.columns(3)
    if w1.button("＋ New workflow", type="primary", use_container_width=True, key="workflow_new"):
        st.session_state["workflow_new_open"] = True
    if w2.button("Playbooks", use_container_width=True, key="workflow_playbooks"):
        nav_to("Playbooks")
    if w3.button("Campaigns", use_container_width=True, key="workflow_campaigns"):
        nav_to("Outreach")
    st.html("""
    <div class="workspace-tabs"><span class="workspace-tab on">Builder</span><span class="workspace-tab">Templates</span><span class="workspace-tab">Active</span><span class="workspace-tab">History</span></div>
    <div class="workflow-canvas">
      <aside class="workflow-tools"><b style="font-size:12px">Add to workflow</b>
        <div class="workflow-tool">⚡ Trigger</div><div class="workflow-tool">◇ Condition</div><div class="workflow-tool">✦ AI research</div><div class="workflow-tool">☷ Add to list</div><div class="workflow-tool">➤ Add to sequence</div><div class="workflow-tool">☑ Create task</div><div class="workflow-tool">◌ Notification</div><div class="workflow-tool">≡ Update field</div>
      </aside>
      <main class="workflow-stage">
        <div class="flow-node"><b>⚡ When this happens</b><span>Organisation matches your approved market criteria</span></div><div class="flow-arrow">↓</div>
        <div class="flow-node"><b>◇ Only if</b><span>Organisation is active, not suppressed and has not already been contacted</span></div><div class="flow-arrow">↓</div>
        <div class="flow-node"><b>✦ Research organisation</b><span>Gather permitted business context and identify the right role</span></div><div class="flow-arrow">↓</div>
        <div class="flow-node"><b>☑ Create next action</b><span>Queue verification or approved outreach depending on campaign rules</span></div>
      </main>
    </div>
    """)

elif st.session_state.page == "Playbooks":
    app_topbar()
    page_header("ENGAGE", "Playbooks", "Turn repeatable market-development processes into guided REACH workflows.")
    st.html("""
    <div class="saved-grid">
      <div class="saved-card"><span class="alert">STARTER</span><h3 style="font-size:14px">New market launch</h3><p>Define market → discover organisations → research decision-makers → prepare outreach.</p></div>
      <div class="saved-card"><b>Unreached market</b><p>Prioritise qualified organisations that have never been contacted.</p></div>
      <div class="saved-card"><b>Interested reply</b><p>Turn a positive reply into a task, meeting and opportunity workflow.</p></div>
    </div>
    """)

elif st.session_state.page == "Enrichment":
    app_topbar()

    st.markdown("""
    <style>
    .enrich-kicker{color:#2EEA7A;font-size:11px;font-weight:800;letter-spacing:.13em;margin-top:4px}
    .enrich-title{font-size:29px;font-weight:820;color:#F4F9F6;line-height:1.1;margin:7px 0 6px}
    .enrich-sub{font-size:13px;color:#8EA297;margin-bottom:16px}
    .enrich-metric{
        min-height:92px;padding:16px;border:1px solid rgba(46,234,122,.12);
        border-radius:12px;background:linear-gradient(145deg,rgba(7,26,17,.95),rgba(3,16,10,.95))
    }
    .enrich-metric b{font-size:25px;color:#F1F8F4}
    .enrich-metric span{display:block;color:#73887c;font-size:11px;margin-top:5px}
    .enrich-section{
        border:1px solid rgba(46,234,122,.13);border-radius:13px;
        background:rgba(4,20,13,.76);padding:18px;margin-top:12px
    }
    .enrich-row{
        display:grid;grid-template-columns:1.2fr 1.7fr .55fr 1fr .8fr;
        gap:12px;align-items:center;padding:12px 3px;border-top:1px solid rgba(255,255,255,.055)
    }
    .enrich-row.head{border-top:0;color:#61776b;font-size:9px;font-weight:800;letter-spacing:.08em}
    .enrich-type{font-size:12px;font-weight:760;color:#EAF5EE}
    .enrich-desc{font-size:11px;color:#8CA096;line-height:1.45}
    .enrich-muted{font-size:11px;color:#B2C1B9}
    .enrich-off{font-size:10px;color:#7B8B83}
    .how-card{min-height:94px;padding:15px;border:1px solid rgba(46,234,122,.12);
        border-radius:11px;background:rgba(7,27,18,.72)}
    .how-num{display:inline-flex;width:30px;height:30px;border-radius:50%;background:#2EEA7A;
        color:#03130b;align-items:center;justify-content:center;font-weight:900;margin-right:8px}
    .how-title{font-size:12px;color:#EDF7F1;font-weight:760}
    .how-copy{font-size:10.5px;color:#7F9589;margin:8px 0 0 40px;line-height:1.45}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="enrich-kicker">ENRICHMENT</div>', unsafe_allow_html=True)
    st.markdown('<div class="enrich-title">Find missing information</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="enrich-sub">Enrich your company and people records with additional data to support your outreach.</div>',
        unsafe_allow_html=True
    )

    a1, a2, a3 = st.columns(3)
    if a1.button("▦  Enrich companies  →", type="primary",
                 use_container_width=True, key="enrich_companies_action"):
        st.session_state.enrichment_target = "companies"
        nav_to("Companies")
    if a2.button("♙  Enrich people  →", use_container_width=True, key="enrich_people_action"):
        st.session_state.enrichment_target = "people"
        nav_to("People")
    if a3.button("⚙  Configure providers  →", use_container_width=True, key="enrich_provider_action"):
        st.session_state.provider_setup_for = "All enrichment"
        nav_to("Settings")

    modes = ["Saved records", "CSV enrichment", "CRM enrichment", "Auto-enrichment"]
    tabs = st.columns([1,1.05,1.1,1.15,3.7])
    for col, mode in zip(tabs[:4], modes):
        with col:
            if st.button(
                mode,
                use_container_width=True,
                type="primary" if st.session_state.enrichment_mode == mode else "secondary",
                key=f"enrich_mode_{mode}"
            ):
                st.session_state.enrichment_mode = mode
                st.rerun()

    company_count = len(st.session_state.get("market_results") or [])
    people_count = len(st.session_state.get("people_results") or [])
    ready_people = sum(
        1 for p in (st.session_state.get("people_results") or [])
        if p.get("email") not in (None, "", "—")
    )

    k1,k2,k3,k4 = st.columns(4)
    metrics = [
        (k1, company_count + people_count, "Records available"),
        (k2, 0, "Updates available"),
        (k3, 0, "Job changes"),
        (k4, ready_people, "Ready for outreach"),
    ]
    for col, value, label in metrics:
        with col:
            st.markdown(
                f'<div class="enrich-metric"><b>{value}</b><span>{label}</span></div>',
                unsafe_allow_html=True
            )

    enrichment_rows = [
        ("▦", "Organisation fields", "Company size, industry, website, address and professional profile data."),
        ("✉", "Work emails", "Professional work email discovery and verification."),
        ("⌕", "Phone numbers", "Direct or switchboard phone numbers where available."),
        ("♙", "Job changes", "Recent role changes and new hires."),
        ("⌘", "Social profiles", "Permitted professional profile links and public business profiles."),
        ("◫", "Technographics", "Tools and technologies used by organisations."),
        ("▥", "Financial data", "Available organisation financial information."),
        ("▤", "News & insights", "Recent organisation news, activity and signals."),
    ]

    st.markdown('<div class="enrich-section">', unsafe_allow_html=True)
    st.markdown(
        '<div class="enrich-row head"><div>ENRICHMENT TYPE</div><div>DESCRIPTION</div>'
        '<div>RECORDS</div><div>PROVIDER</div><div>STATUS</div></div>',
        unsafe_allow_html=True
    )

    # Use Streamlit rows so every Configure action is a real button.
    for i, (icon, name, desc) in enumerate(enrichment_rows):
        r1,r2,r3,r4,r5,r6 = st.columns([1.25,1.85,.55,1,.75,.85])
        r1.markdown(f"**{icon} &nbsp; {name}**")
        r2.caption(desc)
        r3.write(company_count if name == "Organisation fields" else people_count if name == "Work emails" else 0)

        if name == "Work emails" and hunter_is_configured():
            r4.write("Hunter")
            r5.caption("● Connected")
        else:
            r4.write("Not connected")
            r5.caption("● Inactive")

        if r6.button("Configure →", use_container_width=True, key=f"configure_enrichment_{i}"):
            st.session_state.provider_setup_for = name
            nav_to("Settings")

    st.markdown('</div>', unsafe_allow_html=True)

    # Mode-specific meaningful actions.
    if st.session_state.enrichment_mode == "CSV enrichment":
        st.markdown("#### CSV enrichment")
        uploaded_csv = st.file_uploader(
            "Upload a CSV of companies or people",
            type=["csv"],
            key="enrichment_csv_upload"
        )
        if uploaded_csv is not None:
            st.success("CSV loaded. Choose a provider configuration before running enrichment.")
    elif st.session_state.enrichment_mode == "CRM enrichment":
        st.markdown("#### CRM enrichment")
        st.info("Connect a CRM integration to enrich records from your CRM.")
        if st.button("Configure CRM →", key="configure_crm_enrichment"):
            nav_to("Integrations")
    elif st.session_state.enrichment_mode == "Auto-enrichment":
        st.markdown("#### Auto-enrichment")
        st.toggle("Automatically enrich newly verified records", key="auto_enrichment_enabled")
        st.caption("REACH will only run this after a permitted provider and usage rules are configured.")

    st.markdown("### How it works")
    st.caption("Quickly enrich your data in three simple steps.")
    h1,h2,h3 = st.columns(3)
    how = [
        (h1, "1", "Choose enrichment type", "Select the information you want to add to your records."),
        (h2, "2", "Configure provider", "Connect approved data providers and set usage rules."),
        (h3, "3", "Enrich and review", "Run enrichment, review the returned data and choose what to keep."),
    ]
    for col, num, title, copy in how:
        with col:
            st.markdown(
                f'<div class="how-card"><span class="how-num">{num}</span>'
                f'<span class="how-title">{title}</span>'
                f'<div class="how-copy">{copy}</div></div>',
                unsafe_allow_html=True
            )

elif st.session_state.page == "Custom Fields":
    app_topbar()
    page_header("PLATFORM", "Custom fields", "Add fields unique to your market, product and qualification process.")
    st.html("""
    <div class="surface" style="padding:20px;margin-top:14px">
      <div class="home-card-head"><h3>Custom fields</h3><span class="green" style="font-size:10px">+ Create field</span></div>
      <div class="health-row head"><span>Field</span><span>Type</span><span>Object</span><span>Action</span></div>
      <div class="health-row"><b>REACH match reason</b><span>Text</span><span>Company</span><span>Edit</span></div>
      <div class="health-row"><b>Market segment</b><span>Select</span><span>Company</span><span>Edit</span></div>
      <div class="health-row"><b>Opportunity priority</b><span>Select</span><span>Opportunity</span><span>Edit</span></div>
    </div>
    """)


elif st.session_state.page == "Saved Searches":
    app_topbar()
    page_header("PROSPECT & ENRICH", "Saved searches", "Reuse targeting criteria and create alerts when new organisations or people match.")
    st.html("""
    <div class="workspace-tabs"><span class="workspace-tab on">My searches</span><span class="workspace-tab">Shared</span><span class="workspace-tab">Alerts</span></div>
    <div class="saved-grid">
      <div class="saved-card"><span class="alert">ALERT READY</span><h3 style="font-size:14px">Primary market search</h3><p>Save your current company filters and return to the same market view without rebuilding them.</p><span style="font-size:9px;color:#7f8e85">Visibility: Private · Alert: Off</span></div>
      <div class="saved-card"><b>Decision-maker search</b><p>Save job-title, seniority, location and company-fit criteria for people research.</p><span class="green" style="font-size:10px">Create saved search →</span></div>
      <div class="saved-card"><b>Net-new market alert</b><p>Surface newly matching organisations as your underlying data sources change.</p><span class="green" style="font-size:10px">Create alert →</span></div>
    </div>
    """)

# ============================================================
# ADDITIONAL REACH WORKSPACES
# ============================================================

elif st.session_state.page in ["Lists", "Saved Searches", "Emails", "Calls", "Tasks", "Templates",
                               "Meetings", "Conversations", "Pipeline", "Technologies", "Funding",
                               "News & Triggers", "Reports", "Activity", "Team Performance",
                               "Settings", "Help"]:
    app_topbar()
    page = st.session_state.page

    configs = {
        "Lists": ("PROSPECT & ENRICH", "Lists", "Save and organise companies and people into reusable market lists."),
        "Saved Searches": ("PROSPECT & ENRICH", "Saved searches", "Return to your best company and people searches without rebuilding filters."),
        "Emails": ("ENGAGE", "Emails", "Manage outreach emails, replies, opens and campaign activity."),
        "Calls": ("ENGAGE", "Calls", "Keep call activity and outcomes connected to each organisation and opportunity."),
        "Tasks": ("ENGAGE", "Tasks", "Work through research, outreach, follow-up and meeting tasks from one queue."),
        "Templates": ("ENGAGE", "Templates", "Create reusable outreach templates while keeping personalisation in REACH."),
        "Meetings": ("WIN DEALS", "Meetings", "Track booked meetings and connect them to the organisation and opportunity."),
        "Conversations": ("WIN DEALS", "Conversations", "See replies and conversations across your market in one place."),
        "Pipeline": ("WIN DEALS", "Pipeline", "Move interested organisations from first response through to customer."),
        "Technologies": ("RESEARCH & ENRICHMENT", "Technologies", "Use technology signals to understand company fit and personalise research."),
        "Funding": ("RESEARCH & ENRICHMENT", "Funding", "Add funding and growth signals to company research when data sources are connected."),
        "News & Triggers": ("RESEARCH & ENRICHMENT", "News & triggers", "Surface timely company signals that can make outreach more relevant."),
        "Reports": ("ANALYTICS", "Reports", "Create reusable views of market coverage, outreach and opportunity performance."),
        "Activity": ("ANALYTICS", "Activity", "Review market development activity across discovery, research and outreach."),
        "Team Performance": ("ANALYTICS", "Team performance", "A future workspace for shared REACH teams and activity."),
        "Settings": ("ACCOUNT", "Settings", "Configure your market defaults, integrations, sending rules and account preferences."),
        "Help": ("SUPPORT", "Help & support", "Guidance for building markets, researching contacts and using REACH workflows."),
    }
    eyebrow, title, subtitle = configs[page]
    page_header(eyebrow, title, subtitle)

    if page == "Calls":
        st.markdown("""
        <div class="status-tabs"><span class="status-tab on">All calls</span><span class="status-tab">Analytics</span></div>
        <div class="surface" style="padding:22px;margin-top:12px">
          <div style="font-size:18px;font-weight:800">Call contacts and keep outcomes in REACH</div>
          <div style="font-size:12px;color:#839188;margin-top:7px">When calling is connected, each call can be attached to a person, company, disposition, date and opportunity.</div>
          <div class="table-shell" style="margin-top:18px">
            <div class="company-head" style="grid-template-columns:1.2fr 1.2fr .8fr .7fr"><div>Contact</div><div>Company</div><div>Disposition</div><div>Date</div></div>
            <div style="padding:50px;text-align:center;color:#7d8b82;font-size:12px">No call activity yet. Connect a calling workflow to populate this page.</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    elif page == "Tasks":
        st.html("""
        <div class="surface" style="padding:20px;margin-top:14px">
          <div class="home-card-head"><h3>Task queue</h3><span style="font-size:11px;color:#2df58a">Today</span></div>
          <div class="task-item"><div class="act-icon">☑</div><div><b>Review market strategy</b><span>Confirm the organisations REACH should prioritise.</span></div><em>Today</em></div>
          <div class="task-item"><div class="act-icon">♙</div><div><b>Research decision-makers</b><span>Find verified people before outreach.</span></div><em>Next</em></div>
          <div class="task-item"><div class="act-icon">✉</div><div><b>Prepare first sequence</b><span>Review messaging and campaign rules.</span></div><em>Next</em></div>
        </div>
        """)
    elif page == "Pipeline":
        st.html("""
        <div class="metrics4">
          <div class="metricbox"><b>0</b><span>New opportunities</span></div>
          <div class="metricbox blue"><b>0</b><span>Meetings</span></div>
          <div class="metricbox yellow"><b>0</b><span>Proposals</span></div>
          <div class="metricbox green"><b>0</b><span>Won</span></div>
        </div>
        <div class="workspace-tabs"><span class="workspace-tab on">Board</span><span class="workspace-tab">Table</span><span class="workspace-tab">Forecast</span><span class="workspace-tab">Activity</span></div>
        <div class="kanban">
          <div class="kanban-col"><div class="kanban-head">Interested <span>0</span></div><div class="deal-card"><b>No opportunities yet</b><p>Positive replies will enter the pipeline here.</p></div></div>
          <div class="kanban-col"><div class="kanban-head">Meeting <span>0</span></div></div>
          <div class="kanban-col"><div class="kanban-head">Proposal <span>0</span></div></div>
          <div class="kanban-col"><div class="kanban-head">Negotiation <span>0</span></div></div>
          <div class="kanban-col"><div class="kanban-head">Won <span>0</span></div></div>
        </div>
        """)
    else:
        with st.container(border=True):
            st.markdown(f"### {title}")
            st.write(subtitle)
            x1,x2,x3 = st.columns(3)
            if x1.button("＋ Create new", use_container_width=True, key=f"generic_create_{page}"):
                st.session_state[f"generic_created_{page}"] = True
            if x2.button("⚙ Configure", use_container_width=True, key=f"generic_config_{page}"):
                nav_to("Settings")
            if x3.button("✦ Ask REACH AI", use_container_width=True, key=f"generic_ai_{page}"):
                nav_to("AI")
            if st.session_state.get(f"generic_created_{page}"):
                st.info(f"A new {title.lower()} item has been started in this session.")

# ============================================================
# 09 — CLOSING / DEMO END
# ============================================================

elif st.session_state.page == "Closing":
    app_topbar()
    st.markdown("""
    <div class="closing">
      <div class="closing-inner">
        <div class="closing-globe"></div>
        <h1>Turn your market <span class="green">green.</span></h1>
        <p>Your customers are out there. REACH finds them.</p>
        <div class="closing-brand">◉ REACH<span class="green">.</span></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# FALLBACK
# ============================================================

else:
    nav_to("Landing")
