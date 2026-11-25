"""서울 어린이 보행 교통사고 분석 | 산업데이터시각화 개인 프로젝트.

- KRDS 정부 디자인 시스템 참고 UI · Pretendard GOV 웹폰트
- 연도별 영역그래프, 사고 다발지역 추이, 전년 대비 증감
- 자치구 순위, 자치구×연도 히트맵, 연도별 자치구 분포 박스플롯
- 사고 다발지역 지도, 공통 필터, 표 및 CSV 다운로드

필요한 파일: 이 app.py와 동일한 폴더의 CSV 3개.
상단 사진: 안전한_등굣길_횡단보도.png (없으면 텍스트형 헤더로 대체).
외부 데이터 API 키는 필요하지 않습니다.
"""

from pathlib import Path
import html
import base64

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ───────────────────── 0. 앱 설정과 디자인 ─────────────────────
st.set_page_config(
    page_title="서울 어린이 보행 교통사고 분석",
    page_icon="🚸",
    layout="wide",
    initial_sidebar_state="expanded",
)

HERE = Path(__file__).resolve().parent


def load_hero_image():
    """앱 폴더의 횡단보도 사진을 데이터 URL로 변환합니다."""
    photo = HERE / "안전한_등굣길_횡단보도.png"
    if not photo.is_file():
        return ""
    return "data:image/png;base64," + base64.b64encode(photo.read_bytes()).decode("ascii")

NAVY = "#183153"
NAVY_DARK = "#17283F"
BLUE = "#245A89"
TEAL = "#087F8C"
TEAL_LIGHT = "#BFDCE4"
INK = "#222B36"
MUTED = "#526476"
GRID = "#E5EAF0"
BG = "#F6F8FB"
WHITE = "#FFFFFF"
FONT = "Pretendard GOV, Malgun Gothic, Apple SD Gothic Neo, sans-serif"

st.markdown(
    """
    <style>
    /* KRDS(krds.go.kr)의 색상·서체·계층 원칙을 참고한 개인 프로젝트 UI. */
    /* 국내 공공서비스 기본 서체: Pretendard GOV (공식 KRDS 개발자 가이드 CDN). */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-gov-dynamic-subset.min.css');
    :root { color-scheme: light; }
    html, body, .stApp,
    .stApp button, .stApp input, .stApp textarea, .stApp label,
    .stApp [data-testid="stMarkdownContainer"],
    .stApp [data-testid="stMetric"], .stApp [data-testid="stWidgetLabel"] {
        font-family: 'Pretendard GOV', 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif !important;
    }
    .stApp { background: #F6F8FB; color: #222B36; }
    .block-container { max-width: 1460px; padding-top: 1.15rem; padding-bottom: 3rem; }
    [data-testid="stHeader"] { background: rgba(246,248,251,.97); }
    [data-testid="stDecoration"] { display: none; }

    /* 검색 조건 — 흰 바탕·명확한 계층·넉넉한 조작 영역 */
    [data-testid="stSidebar"] {
        background: #FFFFFF; border-right: 1px solid #DDE4EB;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top: 1rem; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] { color: #263747 !important; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #546577 !important; }
    [data-testid="stSidebar"] hr { border-color: #E2E8EE !important; margin: 1.15rem 0; }
    [data-testid="stSidebar"] button[kind="secondary"] {
        background: #FFFFFF !important; color: #214F83 !important;
        border: 1px solid #C6D3E1 !important; border-radius: 5px !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] button[kind="secondary"]:hover {
        background: #EFF5FB !important; border-color: #2A63A4 !important;
    }
    [data-testid="stSidebar"] input[type="radio"] { accent-color: #1E5794; }
    .sidebar-eyebrow { color: #305D88; font-weight: 700; font-size: .81rem; letter-spacing: 0; }
    .sidebar-heading { font-size: 1.40rem; font-weight: 700; color: #172B42;
                       margin: 4px 0 9px; letter-spacing: -.35px; }
    .sidebar-help { color: #536576; font-size: .88rem; line-height: 1.65; margin-bottom: 20px; }
    .sidebar-foot { color: #586B7B; font-size: .81rem; line-height: 1.7; }

    /* 타이포그래피: 제목/본문 두 단계 굵기(700/400), 장식적 영어/배너 최소화 */
    .page-eyebrow { color: #385A79; font-size: .85rem; font-weight: 700; letter-spacing: 0; }
    .page-title { color: #152B45; font-size: clamp(1.8rem, 2.7vw, 2.25rem);
                  font-weight: 700; letter-spacing: -.8px; line-height: 1.34;
                  margin: 8px 0 7px; }
    .page-subtitle { color: #43586A; font-size: .94rem; line-height: 1.65;
                     margin: 0 0 13px; }
    .page-rule { border-bottom: 1px solid #D5DFE8; margin: 15px 0 20px; }
    .pill { display: inline-block; background: transparent; border-right: 1px solid #CFD9E2;
            color: #3E586D; border-radius: 0; font-size: .79rem;
            padding: 2px 13px 2px 0; margin: 0 13px 3px 0; }
    .pill:last-of-type { border: none; }

    /* KPI: 숫자의 정보 위계가 드러나도록 그림자·상단 컬러바 제거 */
    [data-testid="stMetric"] {
        background: #FFFFFF; border: 1px solid #DCE4EC;
        border-radius: 6px; box-shadow: none; padding: 16px 17px 15px;
        min-height: 112px;
    }
    [data-testid="stMetricLabel"] { color: #40566B !important; font-size: .89rem;
                                      font-weight: 400 !important; }
    [data-testid="stMetricValue"] { color: #152B45 !important; font-size: 1.85rem !important;
                                      letter-spacing: -.5px; font-weight: 700 !important; }
    .kpi-caption { color: #506377; font-size: .81rem; line-height: 1.6;
                   margin: 12px 0 11px; }

    /* 동등한 4개 내비게이션 탭 — 버튼에는 넉넉한 클릭 영역 */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        display: flex !important; width: 100% !important; align-items: stretch !important;
        gap: 0 !important; padding: 0 !important;
        border: 1px solid #C9D5E1 !important; border-radius: 6px !important;
        overflow: hidden !important; background: #FFFFFF !important;
        margin: 13px 0 20px !important;
    }
    [data-testid="stTabs"] button[data-baseweb="tab"] {
        flex: 1 1 0 !important; min-width: 0 !important; min-height: 53px !important;
        justify-content: center !important; text-align: center !important;
        padding: 12px 9px !important; background: #FFFFFF !important;
        color: #40566B !important; border: 0 !important;
        border-right: 1px solid #D9E2EB !important;
        border-bottom: 3px solid transparent !important;
        font-weight: 400 !important; border-radius: 0 !important;
        transition: background .12s ease;
    }
    [data-testid="stTabs"] button[data-baseweb="tab"]:last-child { border-right: none !important; }
    [data-testid="stTabs"] button[data-baseweb="tab"] p {
        color: inherit !important; font-size: .92rem !important; font-weight: inherit !important;
        line-height: 1.4 !important; white-space: normal !important;
    }
    [data-testid="stTabs"] button[data-baseweb="tab"]:hover { background: #F1F5FA !important; }
    [data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
        color: #164C86 !important; font-weight: 700 !important;
        background: #EDF4FC !important; border-bottom-color: #245A92 !important;
    }
    [data-testid="stTabs"] button[data-baseweb="tab"]:focus-visible {
        outline: 3px solid #246BEB !important; outline-offset: -3px !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab-highlight"],
    [data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }

    /* 섹션과 차트: 좁은 테두리, 명료한 레이블, 불필요한 장식 제거 */
    .section-label { color: #47647D; font-size: .80rem; font-weight: 700;
                     letter-spacing: 0; margin-bottom: 3px; }
    .section-title { color: #1C334A; font-weight: 700; font-size: 1.35rem;
                     margin: 2px 0 5px; letter-spacing: -.3px; }
    .section-desc { color: #455E73; font-size: .88rem; margin-bottom: 18px;
                    line-height: 1.6; }
    .chart-label { color: #20394F; font-weight: 700; font-size: .99rem;
                   margin: 10px 0 12px; }
    [data-testid="stPlotlyChart"] {
        background: #FFFFFF; border: 1px solid #DFE6ED;
        border-radius: 6px; padding: 6px 6px 1px; box-shadow: none;
    }
    .data-note { background: #F0F5FA; border-left: 3px solid #2D5F91;
                 border-radius: 2px; padding: 12px 15px; color: #344D64;
                 font-size: .86rem; line-height: 1.7; margin: 12px 0; }
    .data-note b { color: #183D62; }
    .insight-card { border: 1px solid #DCE5EC; border-top: 2px solid #446B91;
                    border-radius: 5px; background: white; padding: 18px;
                    color: #40566B; line-height: 1.7; min-height: 150px; font-size: .9rem; }
    .insight-card h4 { color: #1C354C; font-size: 1rem; margin: 0 0 10px; font-weight: 700; }
    .foot-source { color: #526476; font-size: .84rem; line-height: 1.7; }
    .stApp a { color: #1C558F; }
    .stApp a:hover { color: #143E6E; }
    [data-testid="stExpander"] { border-color: #DDE5ED; }
    hr { border-color: #DDE5ED !important; }

    @media (max-width: 920px) {
        .block-container { padding-top: .9rem; }
        .page-title { font-size: 1.7rem; }
        [data-testid="stTabs"] button[data-baseweb="tab"] { padding: 9px 4px !important; min-height: 62px !important; }
        [data-testid="stTabs"] button[data-baseweb="tab"] p { font-size: .81rem !important; }
    }
    @media (max-width: 560px) {
        [data-testid="stTabs"] [data-baseweb="tab-list"] { overflow-x: auto !important; }
        [data-testid="stTabs"] button[data-baseweb="tab"] { flex: 0 0 145px !important; min-width: 145px !important; }
    }

    /* 사진형 헤더: 공공데이터 UI 위계는 유지하되 주제와 연결되는 실사 사진 사용 */
    .photo-hero {
        position: relative;
        min-height: 286px;
        overflow: hidden;
        border: 1px solid #C7D5E2;
        border-radius: 8px;
        margin: 0 0 23px;
        background-color: #152E48;
        background-repeat: no-repeat;
        background-position: center, right center;
        background-size: cover, auto 100%;
        box-shadow: 0 2px 9px rgba(22, 45, 70, .09);
    }
    .photo-hero-content {
        position: relative;
        z-index: 1;
        max-width: 67%;
        padding: 33px 39px 30px;
    }
    .photo-hero-kicker {
        color: #CEE0F2;
        font-size: .82rem;
        font-weight: 500;
        letter-spacing: 0;
        margin-bottom: 11px;
    }
    .photo-hero-title {
        color: #FFFFFF;
        font-size: clamp(1.8rem, 2.6vw, 2.35rem);
        font-weight: 700;
        letter-spacing: -.65px;
        line-height: 1.33;
        margin: 0 0 13px;
    }
    .photo-hero-desc {
        color: #E7EEF5;
        font-size: .95rem;
        font-weight: 400;
        line-height: 1.65;
        margin: 0 0 18px;
        max-width: 680px;
    }
    .photo-hero-meta { display: flex; flex-wrap: wrap; gap: 7px; }
    .photo-hero-meta span {
        display: inline-block;
        font-size: .78rem;
        font-weight: 400;
        color: #E4EBF2;
        border: 1px solid rgba(234, 243, 253, .37);
        border-radius: 4px;
        padding: 5px 9px;
        background: rgba(13, 35, 56, .32);
    }
    @media (max-width: 900px) {
        .photo-hero { min-height: 255px; background-size: cover, auto 100%; }
        .photo-hero-content { max-width: 81%; padding: 26px 24px; }
        .photo-hero-title { font-size: 1.75rem; }
    }
    @media (max-width: 600px) {
        .photo-hero-content { max-width: 100%; padding: 25px 18px; }
        .photo-hero-title { font-size: 1.48rem; }
        .photo-hero-desc { font-size: .85rem; }
        .photo-hero-meta span { font-size: .72rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ───────────────────── 1. 데이터 읽기 ─────────────────────
@st.cache_data(show_spinner=False)
def load_data():
    files = {
        "city": "seoul_child_traffic_city_2010_2025.csv",
        "districts": "seoul_child_traffic_district_2010_2025.csv",
        "hotspots": "seoul_child_hotspots_2012_2025.csv",
    }
    missing = [name for name in files.values() if not (HERE / name).is_file()]
    if missing:
        raise FileNotFoundError("CSV 파일 누락: " + ", ".join(missing))

    city = pd.read_csv(HERE / files["city"], encoding="utf-8-sig")
    districts = pd.read_csv(HERE / files["districts"], encoding="utf-8-sig")
    hotspots = pd.read_csv(HERE / files["hotspots"], encoding="utf-8-sig")
    return city, districts, hotspots


try:
    city, districts, hotspots = load_data()
except (FileNotFoundError, pd.errors.ParserError) as exc:
    st.error(f"데이터 파일을 확인해 주세요. {exc}")
    st.stop()

ALL_DISTRICTS = sorted(districts["자치구"].dropna().unique().tolist())
METRICS = ("사고건수", "부상자수", "사망자수")


# ───────────────────── 2. 공통 분석 조건 ─────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-eyebrow">서울 어린이 보행 교통사고</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-heading">조회 조건</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-help">연도와 지역을 변경하면 주요 지표와 모든 시각화가 함께 변경됩니다.</div>', unsafe_allow_html=True)

    st.markdown("**분석 지역**")
    region_mode = st.radio("분석 지역 선택 방식", ["서울 전체", "자치구 직접 선택"],
                           label_visibility="collapsed", key="region_mode")
    if region_mode == "서울 전체":
        selected_districts = ALL_DISTRICTS
        st.caption("서울 25개 자치구를 포함합니다.")
    else:
        selected_districts = st.multiselect(
            "비교할 자치구", ALL_DISTRICTS,
            default=["강남구"] if "강남구" in ALL_DISTRICTS else ALL_DISTRICTS[:1],
            help="선택한 자치구의 자료만 집계합니다.",
        )

    st.divider()
    st.markdown("**분석 기간**")
    years = st.slider("연도 범위", 2012, 2025, (2012, 2025),
                      label_visibility="collapsed")
    st.caption(f"선택 기간: {years[0]}–{years[1]}년")

    st.divider()
    st.markdown("**비교 지표**")
    metric_label = st.selectbox("사고 비교 지표", list(METRICS),
                                label_visibility="collapsed")
    st.caption("차트의 지표는 사고건수·부상자수·사망자수 중 선택할 수 있습니다.")

    st.divider()
    if st.button("원본 CSV 다시 읽기", use_container_width=True):
        load_data.clear()
        st.rerun()

    st.markdown(
        '<div class="sidebar-foot">자료 기간<br>'
        '전체 사고 통계: 2010–2025<br>'
        '사고 다발지역: 2012–2025<br><br>'
        '분석은 두 자료의 공통 기간인 2012–2025년을 사용합니다.</div>',
        unsafe_allow_html=True,
    )


# ───────────────────── 3. 데이터 필터 및 집계 ─────────────────────
if not selected_districts:
    st.warning("자치구를 한 개 이상 선택해 주세요.")
    st.stop()

view = districts.loc[
    districts["연도"].between(years[0], years[1])
    & districts["자치구"].isin(selected_districts)
].copy()

hotspot_view = hotspots.loc[
    hotspots["연도"].between(years[0], years[1])
    & hotspots["자치구"].isin(selected_districts)
].copy()

if view.empty:
    st.warning("선택한 조건에 해당하는 사고 통계가 없습니다.")
    st.stop()

unit = "건" if metric_label == "사고건수" else "명"
trend = (view.groupby("연도", as_index=False)[metric_label]
         .sum().sort_values("연도"))
trend["연도"] = trend["연도"].astype(int)
trend["증감"] = trend[metric_label].diff()

hotspot_trend = (hotspot_view.groupby("연도").size()
                 .reindex(range(years[0], years[1] + 1), fill_value=0)
                 .rename("기록 수").reset_index())

ranking = (view.groupby("자치구", as_index=False)[metric_label]
           .sum().sort_values([metric_label, "자치구"], ascending=[False, True]))
ranking_top = ranking.head(12).sort_values(metric_label, ascending=True)

matrix = (view.pivot_table(index="자치구", columns="연도", values=metric_label,
                           aggfunc="sum", fill_value=0)
          .reindex(index=sorted(selected_districts),
                   columns=list(range(years[0], years[1] + 1)), fill_value=0))


# ───────────────────── 4. 공통 차트 스타일 및 함수 ─────────────────────
def style_figure(fig, height=365):
    fig.update_layout(
        height=height,
        paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        font=dict(family=FONT, color=INK, size=12),
        margin=dict(l=14, r=20, t=18, b=22),
        hoverlabel=dict(bgcolor="white", font_size=12, font_color=NAVY_DARK),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID, zeroline=False,
                     tickfont=dict(color=MUTED))
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False,
                     tickfont=dict(color=MUTED))
    return fig


def section(number, title, desc):
    st.markdown(f'<div class="section-label">분석 {number}</div>'
                f'<div class="section-title">{title}</div>'
                f'<div class="section-desc">{desc}</div>',
                unsafe_allow_html=True)


def chart_title(text):
    st.markdown(f'<div class="chart-label">{html.escape(text)}</div>',
                unsafe_allow_html=True)


def note(text):
    st.markdown(f'<div class="data-note">{text}</div>', unsafe_allow_html=True)


def create_area_chart():
    # 면적은 사고건수 총량의 시각적 강조용이며, 인구 대비 위험도를 의미하지 않음.
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend["연도"], y=trend[metric_label], mode="lines+markers",
        name=metric_label,
        line=dict(color=BLUE, width=3),
        marker=dict(size=7, color=BLUE, line=dict(color=WHITE, width=1.3)),
        fill="tozeroy", fillcolor="rgba(36,90,137,0.12)",
        hovertemplate=f"%{{x}}년<br>{metric_label}: %{{y:,.0f}}{unit}<extra></extra>",
    ))
    style_figure(fig, 362)
    fig.update_xaxes(title="연도", dtick=1)
    fig.update_yaxes(title=f"{metric_label} ({unit})", rangemode="tozero")
    return fig


def create_hotspot_trend_chart():
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hotspot_trend["연도"], y=hotspot_trend["기록 수"],
        mode="lines+markers", name="다발지역 선정 기록",
        line=dict(color=TEAL, width=2.5),
        marker=dict(size=6, color=TEAL),
        hovertemplate="%{x}년<br>다발지역 선정 기록: %{y:,}개<extra></extra>",
    ))
    style_figure(fig, 325)
    fig.update_xaxes(title="연도", dtick=1)
    fig.update_yaxes(title="선정 기록 수 (개)", rangemode="tozero")
    return fig


def create_yoy_chart():
    # 필터된 기간 내 첫해는 전년도 기준치가 없어 표시하지 않음.
    data = trend.dropna(subset=["증감"]).copy()
    colors = ["#A63E48" if value > 0 else "#245A89" for value in data["증감"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=data["연도"], y=data["증감"],
        marker=dict(color=colors),
        customdata=data[metric_label],
        hovertemplate=("%{x}년<br>전년 대비: %{y:+,.0f}" + unit +
                       "<br>해당 연도: %{customdata:,.0f}" + unit + "<extra></extra>"),
    ))
    style_figure(fig, 325)
    fig.add_hline(y=0, line_color="#97A6B7", line_width=1)
    fig.update_xaxes(title="연도", dtick=1)
    fig.update_yaxes(title=f"전년 대비 증감 ({unit})", zeroline=False)
    return fig


def create_ranking_chart():
    fig = px.bar(
        ranking_top, x=metric_label, y="자치구", orientation="h",
        text=metric_label, color_discrete_sequence=[BLUE],
    )
    fig.update_traces(
        texttemplate="%{x:,.0f}", textposition="outside", cliponaxis=False,
        hovertemplate=f"%{{y}}<br>{metric_label}: %{{x:,.0f}}{unit}<extra></extra>",
        marker_line_width=0,
    )
    style_figure(fig, 485)
    fig.update_layout(margin=dict(l=8, r=57, t=15, b=24))
    fig.update_xaxes(title=f"{metric_label} ({unit})", showgrid=True,
                     gridcolor=GRID, rangemode="tozero")
    fig.update_yaxes(title="", showgrid=False, categoryorder="array",
                     categoryarray=ranking_top["자치구"].tolist())
    return fig


def create_heatmap(show_numbers=False):
    colors = [[0.0, "#F2F7FB"], [0.32, "#C8DAEC"],
              [0.68, "#729FC7"], [1.0, "#245A89"]]
    fig = px.imshow(
        matrix, aspect="auto", color_continuous_scale=colors,
        labels={"x": "연도", "y": "자치구", "color": f"{metric_label} ({unit})"},
        text_auto=",.0f" if show_numbers else False,
    )
    fig.update_traces(
        hovertemplate=f"%{{y}} · %{{x}}년<br>{metric_label}: %{{z:,.0f}}{unit}<extra></extra>"
    )
    fig.update_layout(
        height=max(355, min(865, len(selected_districts) * 28 + 135)),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family=FONT, color=INK, size=11),
        margin=dict(l=26, r=17, t=12, b=26),
        coloraxis_colorbar=dict(title=unit, thickness=13),
    )
    fig.update_xaxes(type="category", side="bottom", title="연도",
                     tickangle=0, showgrid=False)
    fig.update_yaxes(type="category", title="자치구", autorange="reversed",
                     showgrid=False)
    return fig


def create_boxplot():
    # 한 해에 25개 구의 사고건수 25개 값 → 중앙값·IQR·이상치.
    # 개별 사고 기록 1건씩을 분포로 표현한 것이 절대 아님.
    chart_df = view[["연도", "자치구", metric_label]].copy()
    chart_df["연도표기"] = chart_df["연도"].astype(str)
    fig = px.box(
        chart_df, x="연도표기", y=metric_label, points="outliers",
        color_discrete_sequence=[BLUE],
        labels={"연도표기": "연도", metric_label: f"자치구별 {metric_label} ({unit})"},
    )
    fig.update_traces(
        marker=dict(color=TEAL, size=6),
        line=dict(color=BLUE, width=1.7),
        fillcolor="rgba(36,90,137,0.18)",
    )
    style_figure(fig, 390)
    fig.update_xaxes(title="연도", categoryorder="array",
                     categoryarray=[str(y) for y in range(years[0], years[1] + 1)])
    fig.update_yaxes(title=f"자치구별 {metric_label} ({unit})", rangemode="tozero")
    return fig


def create_hotspot_map():
    center = {
        "lat": float(hotspot_view["위도"].mean()),
        "lon": float(hotspot_view["경도"].mean()),
    }
    zoom = 11 if len(selected_districts) <= 3 else 10
    fig = px.scatter_map(
        hotspot_view, lat="위도", lon="경도", size="사고건수",
        color="사고건수", size_max=18,
        color_continuous_scale=[[0, "#DDEBF5"], [.5, "#6297C0"], [1, "#214E7B"]],
        hover_name="장소",
        hover_data={"연도": True, "자치구": True, "사고건수": True,
                    "사상자수": True, "위도": False, "경도": False,
                    "사고다발지fid": False},
        zoom=zoom, center=center, height=605,
    )
    fig.update_layout(
        map_style="open-street-map",
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="white",
        coloraxis_colorbar=dict(title="사고건수", thickness=14),
        font=dict(family=FONT, color=INK),
    )
    return fig


# ───────────────────── 5. 페이지 헤더와 핵심 지표 ─────────────────────
hero_data_url = load_hero_image()
if hero_data_url:
    # 짙은 청색 그라데이션으로 글자 가독성을 확보하고,
    # 사진을 오른쪽에 원본 비율로 배치하여 인물 머리가 잘리지 않게 합니다.
    hero_style = (
        "background-image: linear-gradient(90deg, "
        "#152E48 0%, rgba(21,46,72,.99) 27%, "
        "rgba(21,46,72,.91) 44%, rgba(21,46,72,.54) 65%, "
        "rgba(21,46,72,.12) 88%, rgba(21,46,72,.03) 100%), "
        f"url('{hero_data_url}');"
    )
    st.markdown(
        f"""<div class="photo-hero" style="{hero_style}">
            <div class="photo-hero-content">
                <div class="photo-hero-kicker">서울시 교통안전 데이터 분석 · 개인 프로젝트</div>
                <div class="photo-hero-title">서울 어린이 보행 교통사고<br>시공간 분석 대시보드</div>
                <div class="photo-hero-desc">연도별 사고 추이와 자치구별 차이, 사고 다발지역의<br>
                공간 분포를 공개데이터로 분석합니다.</div>
                <div class="photo-hero-meta">
                    <span>2012–2025년</span>
                    <span>서울 25개 자치구</span>
                    <span>한국도로교통공단 공개데이터</span>
                </div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
else:
    # 사진을 아직 GitHub에 올리지 않은 경우에도 앱이 정상 실행되도록 유지
    st.markdown(
        '<div class="page-eyebrow">공공데이터 기반 시공간 분석 · 개인 프로젝트</div>'
        '<div class="page-title">서울 어린이 보행 교통사고 분석</div>'
        '<div class="page-subtitle">연도별 추이와 자치구 간 차이, 사고 다발지역의 공간 분포를 살펴봅니다.</div>'
        '<div class="pill">공통 분석 기간 2012–2025년</div>'
        '<div class="pill">서울 25개 자치구</div>'
        '<div class="pill">한국도로교통공단 공개데이터</div>'
        '<div class="page-rule"></div>',
        unsafe_allow_html=True,
    )

c1, c2, c3, c4 = st.columns(4, gap="medium")
c1.metric(f"선택 기간 {metric_label}", f"{view[metric_label].sum():,}{unit}")

if len(trend) > 1 and trend[metric_label].iloc[0] > 0:
    first = float(trend[metric_label].iloc[0])
    last = float(trend[metric_label].iloc[-1])
    change = (last - first) / first * 100
    c2.metric("첫해 대비 마지막해", f"{change:+.1f}%",
              help=f"{years[0]}년 {first:,.0f}{unit} → {years[1]}년 {last:,.0f}{unit}")
else:
    c2.metric("첫해 대비 마지막해", "—",
              help="한 해만 선택하거나 첫해 값이 0이면 변화율을 산출하지 않습니다.")

c3.metric("사고 다발지역 선정 기록", f"{len(hotspot_view):,}개")
c4.metric("선택한 자치구", f"{len(selected_districts):,}개")
st.markdown(
    '<div class="kpi-caption">※ 사고 다발지역은 연도별 선정 기록의 합계입니다. '
    '중복되지 않는 장소의 수나 모든 사고 발생 지점을 뜻하지 않습니다.</div>',
    unsafe_allow_html=True,
)


# ───────────────────── 6. 분석 탭: 7개 시각화 ─────────────────────
tab_trend, tab_region, tab_map, tab_insight = st.tabs([
    "01  연도별 변화", "02  지역 비교·분포", "03  사고 다발지역 지도", "04  분석 결과·원자료",
])

with tab_trend:
    section("01", "연도별 변화", "장기적인 사고 추세뿐 아니라 해마다 증가했는지, 감소했는지도 확인합니다.")

    chart_title(f"연도별 {metric_label} · 영역그래프")
    st.plotly_chart(create_area_chart(), use_container_width=True,
                    config={"displayModeBar": False})

    left, right = st.columns(2, gap="medium")
    with left:
        chart_title("연도별 사고 다발지역 선정 기록")
        st.plotly_chart(create_hotspot_trend_chart(), use_container_width=True,
                        config={"displayModeBar": False})
    with right:
        chart_title(f"전년 대비 {metric_label} 증감")
        if len(trend) > 1:
            st.plotly_chart(create_yoy_chart(), use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.info("한 해만 선택하면 전년 대비 변화량을 계산할 수 없습니다. 분석 기간을 넓혀 보세요.")

    if len(trend) > 1 and trend[metric_label].iloc[0] > 0:
        note(f"<b>기간 변화:</b> {years[0]}년 {trend[metric_label].iloc[0]:,.0f}{unit} → "
             f"{years[1]}년 {trend[metric_label].iloc[-1]:,.0f}{unit} "
             f"({change:+.1f}%). 장기 변화율과 전년 대비 증감은 서로 다른 지표이며, "
             "감소 원인을 이 데이터만으로 단정할 수는 없습니다.")
    else:
        note("전년 대비 그래프의 첫 막대는 선택한 기간에서 두 번째 연도부터 표시됩니다.")

with tab_region:
    section("02", "자치구별 차이와 분포", "지역별 총량, 연도별 집중도, 자치구 간 분포를 서로 다른 그래프로 확인합니다.")

    chart_title(f"자치구별 {metric_label} 합계 · 상위 12개")
    st.plotly_chart(create_ranking_chart(), use_container_width=True,
                    config={"displayModeBar": False})
    st.caption("상위 12개만 그래프에 표시하며, 모든 자치구의 값은 '분석 결과·원자료' 탭에서 확인할 수 있습니다.")

    st.divider()
    chart_title("자치구 × 연도 히트맵")
    show_numbers = st.checkbox("히트맵에 실제 수치 표시", value=False)
    st.plotly_chart(create_heatmap(show_numbers), use_container_width=True,
                    config={"displayModeBar": False})
    st.caption("각 칸은 해당 자치구의 해당 연도에 집계된 선택 지표입니다. 진한 색일수록 값이 큽니다.")

    st.divider()
    chart_title(f"연도별 자치구 {metric_label} 분포 · 박스플롯")
    st.plotly_chart(create_boxplot(), use_container_width=True,
                    config={"displayModeBar": False})
    if len(selected_districts) < 5:
        st.info("현재 선택한 자치구 수가 적어 상자 분포의 해석이 제한적입니다. '서울 전체'를 선택하면 25개 자치구의 분포를 비교할 수 있습니다.")
    note("<b>박스플롯 해석:</b> 각 연도의 점들은 자치구별 집계값이며, "
         "상자는 자치구 사이의 중앙값과 중간 50% 분포를 나타냅니다. "
         "어린이 인구·보행량으로 표준화한 지역별 사고 위험도는 아닙니다.")

with tab_map:
    section("03", "사고 다발지역 위치", "공개데이터에서 사고 다발지역으로 선정된 지점의 대표 좌표를 지도에서 확인합니다.")
    if hotspot_view.empty:
        st.info("선택한 조건에는 사고 다발지역 선정 기록이 없습니다. 연도·지역 조건을 바꿔 보세요.")
    else:
        st.plotly_chart(
            create_hotspot_map(), use_container_width=True,
            config={"displayModeBar": True, "scrollZoom": True},
        )
        st.caption("지도 안에서 두 손가락 위아래 스크롤 또는 마우스 휠로 확대·축소할 수 있습니다. 터치패드 두 손가락 벌리기는 브라우저 전체 확대가 될 수 있습니다.")
        chart_title("선택한 조건의 사고 다발지역 기록 · 사고건수 상위 10개")
        shown = ["연도", "자치구", "장소", "사고건수", "사상자수"]
        st.dataframe(
            hotspot_view.sort_values(["사고건수", "사상자수"], ascending=[False, False])[shown].head(10),
            hide_index=True, use_container_width=True,
        )
    note("<b>지도 해석 주의:</b> 여기에는 모든 교통사고의 실제 발생 위치가 아닌 "
         "'사고 다발지역 선정 기록'의 대표 좌표만 표시됩니다. "
         "마커 크기와 색상은 해당 선정 기록에 기재된 사고건수입니다.")

with tab_insight:
    section("04", "주요 발견과 원자료", "선택 조건의 요약 결과를 확인하고, 분석에 활용한 자료를 내려받을 수 있습니다.")

    latest = trend.iloc[-1]
    earliest = trend.iloc[0]
    top_region = ranking.iloc[0]
    top_name = html.escape(str(top_region["자치구"]))
    summary_change = "한 해만 선택" if len(trend) < 2 else (
        f"{change:+.1f}%" if earliest[metric_label] > 0 else "계산 불가"
    )

    one, two, three = st.columns(3, gap="medium")
    with one:
        st.markdown(
            '<div class="insight-card"><h4>01 · 기간별 변화</h4>'
            f'{int(earliest["연도"])}년 {earliest[metric_label]:,.0f}{unit} → '
            f'{int(latest["연도"])}년 {latest[metric_label]:,.0f}{unit}<br>'
            f'<b>첫해 대비 {summary_change}</b><br>'
            '증감 추이의 원인을 이 자료만으로 판단할 수는 없습니다.</div>',
            unsafe_allow_html=True,
        )
    with two:
        st.markdown(
            '<div class="insight-card"><h4>02 · 자치구별 비교</h4>'
            f'선택 조건에서 합계가 가장 큰 자치구는 <b>{top_name}</b>입니다.<br>'
            f'{metric_label} <b>{top_region[metric_label]:,.0f}{unit}</b><br>'
            '인구 규모 차이까지 반영한 순위는 아닙니다.</div>',
            unsafe_allow_html=True,
        )
    with three:
        st.markdown(
            '<div class="insight-card"><h4>03 · 사고 다발지역</h4>'
            f'현재 조건의 선정 기록은 <b>{len(hotspot_view):,}개</b>입니다.<br>'
            '연도별 선정 기록의 합계이며 고유 장소 수나 전체 사고 위치 수는 아닙니다.</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("#### 데이터 검산 및 다운로드")
    with st.expander("연도별 선택 지표 집계표", expanded=False):
        st.dataframe(trend, hide_index=True, use_container_width=True)
    with st.expander("자치구별 전체 집계표", expanded=False):
        st.dataframe(view.sort_values(["연도", "자치구"]),
                     hide_index=True, use_container_width=True)
        st.download_button(
            "선택 조건의 자치구 사고 통계 CSV 다운로드",
            data=view.to_csv(index=False).encode("utf-8-sig"),
            file_name="selected_district_accidents.csv", mime="text/csv",
        )
    with st.expander("사고 다발지역 원자료", expanded=False):
        st.dataframe(hotspot_view.sort_values(["연도", "자치구"]),
                     hide_index=True, use_container_width=True)
        st.download_button(
            "선택 조건의 사고 다발지역 CSV 다운로드",
            data=hotspot_view.to_csv(index=False).encode("utf-8-sig"),
            file_name="selected_hotspots.csv", mime="text/csv",
        )
    with st.expander("서울시 연도별 합계와 자치구 합계 검산", expanded=False):
        aggregated_city = (districts.groupby("연도", as_index=False)[list(METRICS)]
                           .sum().sort_values("연도"))
        city_compare = city.merge(aggregated_city, on="연도", suffixes=("_서울", "_자치구합"))
        city_compare["사고건수차이"] = city_compare["사고건수_서울"] - city_compare["사고건수_자치구합"]
        st.dataframe(city_compare, hide_index=True, use_container_width=True)
        if city_compare["사고건수차이"].eq(0).all():
            st.success("전체 기간의 연도별 사고건수에서 서울시 합계와 자치구 합계가 일치합니다.")
        else:
            st.warning("일부 연도의 서울시 합계와 자치구 합계가 다릅니다. 원자료를 확인해 주세요.")

    st.markdown("#### 분석의 범위와 한계")
    note("어린이 인구와 보행량을 반영하지 않은 사고건수 비교이므로 <b>인구 대비 사고 위험도</b>를 직접 나타내지는 않습니다. "
         "사고 다발지역 자료에는 선정 기준과 시기 차이가 있을 수 있으며, "
         "그래프는 상관·분포를 보여줄 뿐 교통안전 정책의 인과적 효과를 증명하지 않습니다.")

    st.markdown("#### 데이터 출처 및 디자인 참고")
    st.markdown(
        "[한국도로교통공단 지자체별 대상사고 통계](https://opendata.koroad.or.kr/api/selectSttDataSet.do)"
        " · [한국도로교통공단 보행어린이 사고 다발지역](https://opendata.koroad.or.kr/api/selectChildDataSet.do)"
    )
    st.markdown("[대한민국 정부 디자인 시스템(KRDS)](https://www.krds.go.kr/)의 글꼴·색상·레이아웃 원칙을 참고했습니다. "
                "본 대시보드는 수업용 개인 프로젝트이며 공공기관 공식 서비스가 아닙니다.")
    st.markdown(
        '<div class="foot-source">전체 통계는 어린이보행사고만 추출했습니다. '
        '지역별 분석 및 다발지역 자료의 공통 기간은 2012–2025년입니다. '
        '박스플롯의 관측 단위는 개별 사고가 아니라 자치구별 연도 집계값입니다.</div>',
        unsafe_allow_html=True,
    )
