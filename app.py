"""산업데이터시각화 개인 프로젝트 | 서울 어린이 보행 교통사고 분석

11주차: @st.cache_data → 사이드바 위젯 → 필터링 → 지표/Plotly → 표/CSV 저장
12주차: app.py 기준 상대 경로, GitHub + Streamlit Community Cloud 배포
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="서울 어린이 보행 교통사고 | 데이터 대시보드",
    page_icon="🚸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ────────── 디자인 설정 ──────────
# B안: 교통안전 인포그래픽형 팔레트 (정보/분석 로직은 기존과 동일)
NAVY = "#152F4B"             # 바탕과 제목
TEAL = "#D9535B"             # 사고건수 추이/지역별 비교: 코랄 레드
ORANGE = "#CA8400"           # 다발지역 추이: 명도 대비가 있는 앰버
SAFETY_YELLOW = "#FFC64A"    # 교통안전 강조 포인트
MUTED = "#69788A"
GRID = "#EBEFF5"
PAPER = "#FFFFFF"

st.markdown(
    """
    <style>
    /* B안: 교통안전 인포그래픽. 데이터 처리·위젯·차트 개수·지도는 변경하지 않음. */
    :root {color-scheme: light;}
    .stApp {background: #F6F8FC; color: #172B41;}
    .block-container {max-width: 1470px; padding-top: 1.1rem; padding-bottom: 3.4rem;}

    /* 교통안전 테마 사이드바: 깊은 남색 + 노란색 포인트 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #183651 0%, #102B46 100%);
        border-right: 1px solid #294761;
    }
    [data-testid="stSidebar"] .block-container {padding-top: 1.55rem;}
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] .stRadio label p,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #E4ECF6 !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {font-size: .89rem;}
    [data-testid="stSidebar"] hr {border-color: rgba(255,255,255,.18) !important;}
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {font-weight: 650;}
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
        border: 1px solid #F8C148;
        background: #F8C148;
        color: #26354A;
        font-weight: 750;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
        border-color: #FFE18A; background: #FFE18A;
    }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"],
    [data-testid="stSidebar"] [data-testid="stMultiSelect"] [data-baseweb="select"] {
        background: #FFFFFF; border-radius: 9px;
    }
    .sidebar-title {
        font-size: 1.05rem; font-weight: 850; color: #FFC64A;
        letter-spacing: -.25px; padding: 0 0 8px;
        border-bottom: 2px solid rgba(255,198,74,.85); margin-bottom: 11px;
    }
    .sidebar-subtitle {font-size: .81rem; color: #C4D4E3; line-height: 1.55; margin-bottom: 18px;}

    /* 콤팩트한 안전 인포그래픽 헤더: 발표 첫 화면에 차트가 더 많이 보이도록 */
    .hero {
        position: relative; overflow: hidden;
        background: linear-gradient(115deg, #102A45 0%, #183D5A 100%);
        border-radius: 17px; padding: 25px 33px 23px;
        margin-bottom: 13px; border-bottom: 5px solid #FFC64A;
        box-shadow: 0 10px 25px rgba(14,44,73,.11);
    }
    .hero:before {
        content: ""; position: absolute; width: 210px; height: 15px; right: 24px; top: 0;
        background: repeating-linear-gradient(115deg, #FFC64A 0 22px, transparent 22px 33px);
        opacity: .95;
    }
    .hero .eyebrow {
        font-size: .73rem; font-weight: 850; letter-spacing: 1.55px;
        color: #FFD274; margin-bottom: 8px;
    }
    .hero h1 {
        color: white; font-size: clamp(1.6rem, 2.6vw, 2.30rem);
        font-weight: 850; letter-spacing: -1.1px; margin: 0 0 9px; line-height: 1.29;
    }
    .hero h1 span {color: #FFCF61;}
    .hero p {font-size: .96rem; color: #EDF3FB; line-height: 1.62; margin: 0;}
    .hero .meta {margin-top: 14px; display: flex; flex-wrap: wrap; gap: 7px;}
    .hero .meta span {
        font-size: .76rem; color: #EAF1F7; padding: 5px 10px;
        background: rgba(255,255,255,.08); border-radius: 20px;
        border: 1px solid rgba(255,255,255,.24);
    }
    .hero .safety-mark {color: #FFCE5D; margin-right: 5px;}

    /* KPI: 결과 색상만 강조하고, 지표 자체의 의미는 그대로 */
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #E5EAF1;
        border-top: 4px solid #E65D62;
        border-radius: 14px; padding: 16px 18px 13px;
        box-shadow: 0 4px 15px rgba(20,47,75,.045);
        min-height: 110px;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(2) div[data-testid="stMetric"] {border-top-color: #FFBF3D;}
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(3) div[data-testid="stMetric"] {border-top-color: #E88137;}
    div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(4) div[data-testid="stMetric"] {border-top-color: #286B93;}
    [data-testid="stMetricLabel"] {font-size: .87rem; color: #5E6F80; font-weight: 650;}
    [data-testid="stMetricValue"] {color: #1A3651; font-weight: 820; letter-spacing: -.6px;}

    .section-head {margin: 25px 0 4px; display:flex; align-items:center; gap:10px;}
    .section-head .num {
        display:inline-flex; align-items:center; justify-content:center;
        width:29px; height:29px; flex: 0 0 29px;
        border-radius: 8px; background: #FFE7A8;
        border: 1px solid #F6D17A; color: #614613; font-size: .78rem; font-weight: 900;
    }
    .section-head h2 {font-size: 1.16rem; letter-spacing: -.3px; color: #183550; margin: 0; font-weight: 820;}
    .section-intro {font-size: .88rem; color: #66788A; margin: 0 0 13px;}
    .small-note {font-size: .81rem; color: #66788A; margin: 8px 0 13px;}
