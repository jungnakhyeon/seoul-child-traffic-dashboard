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
    .note {
        padding: 16px 18px; border-left: 5px solid #FFC64A;
        background: #FFF8E9; border-radius: 0 12px 12px 0;
        font-size: .89rem; line-height: 1.75; color: #35465A;
    }
    .note b {color: #253D54;}

    /* 차트·지도의 틀에만 스타일을 적용, Plotly 값/축/마커는 그대로 */
    [data-testid="stPlotlyChart"] {
        background: white; border: 1px solid #E5EAF1;
        border-radius: 14px; padding: 7px 6px 3px;
        box-shadow: 0 4px 14px rgba(20,47,75,.035);
    }
    [data-testid="stExpander"] {border-radius: 12px; border-color: #E0E7F0;}
    .stApp a {color: #1D5E8C;}
    .stApp a:hover {color: #C45357;}
    hr {border-color: #E1E7EF !important;}

    @media (max-width: 800px) {
        .hero {padding: 22px 18px 17px; border-radius: 14px;}
        .hero:before {right: 0; width: 100px;}
        .hero h1 {font-size: 1.47rem;}
        .block-container {padding-top: .8rem;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

HERE = Path(__file__).parent


# ────────── 11주차 2-1: 상대 경로, 캐시 ──────────
@st.cache_data
def load_data():
    city = pd.read_csv(HERE / "seoul_child_traffic_city_2010_2025.csv")
    districts = pd.read_csv(HERE / "seoul_child_traffic_district_2010_2025.csv")
    hotspots = pd.read_csv(HERE / "seoul_child_hotspots_2012_2025.csv")
    return city, districts, hotspots


city, districts, hotspots = load_data()
ALL_DISTRICTS = sorted(districts["자치구"].dropna().unique().tolist())

# ────────── 11주차 2-2: 사이드바 위젯 ──────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">분석 조건</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtitle">기간과 지역을 선택하면 숫자와 모든 차트, 지도가 함께 변경됩니다.</div>', unsafe_allow_html=True)
    region_mode = st.radio("분석 지역", ["서울 전체", "자치구 직접 선택"], index=0)
    if region_mode == "서울 전체":
        selected_districts = ALL_DISTRICTS
        st.caption("서울 25개 자치구를 모두 포함합니다.")
    else:
        selected_districts = st.multiselect(
            "비교할 자치구", ALL_DISTRICTS, default=["강남구"],
            help="한 개 이상 선택하면 선택한 구만 차트와 지도에 표시됩니다.",
        )
    st.divider()
    years = st.slider("분석 기간", min_value=2012, max_value=2025, value=(2012, 2025))
    metric_label = st.selectbox("차트 비교 지표", ["사고건수", "부상자수", "사망자수"])
    st.divider()
    if st.button("원본 CSV 다시 읽기", use_container_width=True):
        load_data.clear()
        st.rerun()
    st.caption("전체 사고 통계: 2010–2025\n\n사고 다발지역: 2012–2025\n\n두 자료의 공통 기간으로 필터링합니다.")

# ────────── 헤더 ──────────
st.markdown(
    """
    <div class="hero">
      <div class="eyebrow"><span class="safety-mark">🚸</span> ROAD SAFETY / DATA STORY · SEOUL</div>
      <h1>서울 어린이 보행 교통사고<br><span>시공간 분석 대시보드</span></h1>
      <p>교통사고는 언제 줄었을까? 사고가 집중된 곳은 어디일까?<br>
      연도별 발생 추이와 사고 다발지역 분포를 두 가지 공공데이터로 살펴봅니다.</p>
      <div class="meta"><span>2012–2025년 공통 분석</span><span>서울 25개 자치구</span><span>한국도로교통공단 공개데이터</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ────────── 11주차 2-3: 위젯 값 → view → 지표/차트/표 ──────────
view = districts.loc[
    districts["자치구"].isin(selected_districts)
    & districts["연도"].between(*years)
].copy()
hotspot_view = hotspots.loc[
    hotspots["자치구"].isin(selected_districts)
    & hotspots["연도"].between(*years)
].copy()

if not selected_districts or view.empty:
    st.warning("표시할 데이터가 없습니다. 사이드바에서 자치구를 하나 이상 선택해 주세요.")
    st.stop()

unit = "건" if metric_label == "사고건수" else "명"
trend = view.groupby("연도", as_index=False)[metric_label].sum().sort_values("연도")
hotspot_trend = (
    hotspot_view.groupby("연도").size()
    .reindex(range(years[0], years[1] + 1), fill_value=0)
    .rename("기록 수").reset_index()
)
ranking = (
    view.groupby("자치구", as_index=False)[metric_label]
    .sum().sort_values(metric_label, ascending=False)
)
ranking_top = ranking.head(12).sort_values(metric_label, ascending=True)

# ────────── 11주차 3-1: 지표 카드 ──────────
st.markdown('<div class="section-head"><span class="num">01</span><h2>핵심 지표</h2></div>', unsafe_allow_html=True)
st.markdown('<div class="section-intro">선택한 기간과 지역의 집계값입니다.</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4, gap="medium")
c1.metric(f"선택 기간 {metric_label}", f"{view[metric_label].sum():,}{unit}")
if len(trend) > 1 and trend[metric_label].iloc[0] > 0:
    start_value = trend[metric_label].iloc[0]
    end_value = trend[metric_label].iloc[-1]
    change = (end_value - start_value) / start_value * 100
    c2.metric("첫해 대비 마지막해", f"{change:+.1f}%", help=f"{years[0]}년 {start_value:,.0f}{unit} → {years[1]}년 {end_value:,.0f}{unit}")
else:
    c2.metric("첫해 대비 마지막해", "—", help="1개 연도만 선택했거나 첫해 값이 0이면 계산하지 않습니다.")
c3.metric("사고 다발지역 기록", f"{len(hotspot_view):,}개")
c4.metric("선택 자치구", f"{len(selected_districts):,}개")
st.markdown('<div class="small-note">※ 다발지역 수는 연도별 선정 기록을 합한 값으로, 서로 다른 장소의 고유 개수가 아닙니다.</div>', unsafe_allow_html=True)

# ────────── Plotly 공통 디자인 ──────────
def style_figure(fig, height=350, *, show_y_zero=False):
    fig.update_layout(
        height=height,
        paper_bgcolor=PAPER, plot_bgcolor=PAPER,
        font=dict(family="Arial, Malgun Gothic, sans-serif", color=NAVY, size=12),
        margin=dict(l=10, r=12, t=30, b=12),
        hoverlabel=dict(bgcolor="white", font_size=13, font_color=NAVY),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=GRID, tickfont=dict(color=MUTED))
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=show_y_zero, rangemode="tozero", tickfont=dict(color=MUTED))
    return fig


def section(index, title, description):
    st.markdown(
        f'<div class="section-head"><span class="num">{index}</span><h2>{title}</h2></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="section-intro">{description}</div>', unsafe_allow_html=True)


# ────────── 11주차 3-2, 3-3: Plotly 차트, 두 열 배치 ──────────
section("02", "시간에 따른 변화", "전체 사고 추이와 사고 다발지역 선정 기록을 나란히 비교합니다.")
col_left, col_right = st.columns(2, gap="large")

with col_left:
    st.markdown(f"**연도별 {metric_label} 추이**")
    fig_trend = px.line(
        trend, x="연도", y=metric_label, markers=True,
        labels={"연도": "연도", metric_label: f"{metric_label} ({unit})"},
        color_discrete_sequence=[TEAL],
    )
    fig_trend.update_traces(
        line=dict(width=3.1), marker=dict(size=8, line=dict(color="white", width=1.5)),
        hovertemplate=f"%{{x}}년<br>{metric_label}: %{{y:,.0f}}{unit}<extra></extra>",
    )
    fig_trend.update_xaxes(dtick=1, tickangle=0)
    style_figure(fig_trend)
    st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})

with col_right:
    st.markdown("**연도별 사고 다발지역 기록 수**")
    fig_hotspot = px.line(
        hotspot_trend, x="연도", y="기록 수", markers=True,
        labels={"연도": "연도", "기록 수": "다발지역 기록 (개)"},
        color_discrete_sequence=[ORANGE],
    )
    fig_hotspot.update_traces(
        line=dict(width=3.1), marker=dict(size=8, line=dict(color="white", width=1.5)),
        hovertemplate="%{x}년<br>다발지역 기록: %{y:,.0f}개<extra></extra>",
    )
    fig_hotspot.update_xaxes(dtick=1)
    style_figure(fig_hotspot)
    st.plotly_chart(fig_hotspot, use_container_width=True, config={"displayModeBar": False})

section("03", "자치구별 비교", f"선택한 기간의 {metric_label} 합계가 큰 자치구를 비교합니다. 지역별 인구·보행량 차이는 반영하지 않았습니다.")
fig_rank = px.bar(
    ranking_top, x=metric_label, y="자치구", orientation="h",
    color_discrete_sequence=[TEAL],
    labels={metric_label: f"{metric_label} ({unit})", "자치구": ""},
    text=metric_label,
)
fig_rank.update_traces(
    marker=dict(color=TEAL, line=dict(width=0)),
    texttemplate="%{x:,.0f}", textposition="outside", cliponaxis=False,
    hovertemplate=f"%{{y}}<br>{metric_label}: %{{x:,.0f}}{unit}<extra></extra>",
)
style_figure(fig_rank, height=455)
fig_rank.update_layout(margin=dict(l=12, r=55, t=12, b=15))
fig_rank.update_xaxes(showgrid=True, gridcolor=GRID, rangemode="tozero")
fig_rank.update_yaxes(showgrid=False, categoryorder="array", categoryarray=ranking_top["자치구"].tolist())
st.plotly_chart(fig_rank, use_container_width=True, config={"displayModeBar": False})
st.caption("상위 12개 자치구만 표시했습니다. 모든 자치구의 값은 아래 원자료 표에서 확인할 수 있습니다.")

# 선택한 조건에서 팩트만 자동 요약. 인과관계와 위험도를 단정하지 않음.
if not ranking.empty:
    most = ranking.iloc[0]
    if len(trend) > 1:
        note1 = (
            f"선택 지표는 <b>{years[0]}년 {trend[metric_label].iloc[0]:,.0f}{unit}</b>에서 "
            f"<b>{years[1]}년 {trend[metric_label].iloc[-1]:,.0f}{unit}</b>으로 변했습니다."
        )
    else:
        note1 = f"{years[0]}년의 선택 지표 합계는 <b>{trend[metric_label].iloc[0]:,.0f}{unit}</b>입니다."
    note2 = f"선택 기간에서 <b>{most['자치구']}</b>의 {metric_label} 합계가 가장 높습니다 ({most[metric_label]:,.0f}{unit})."
    st.markdown(
        '<div class="note"><b>데이터가 보여주는 점</b><br>' + note1 + " " + note2 + "<br>"
        '※ 이것만으로 사고 증감의 원인이나 해당 자치구의 상대적 위험도를 단정할 수는 없습니다.</div>',
        unsafe_allow_html=True,
    )

section("04", "사고 다발지역 지도", "점 하나는 특정 연도에 선정된 사고 다발지역 기록입니다. 마커 크기는 해당 기록의 사고건수에 비례합니다.")
if hotspot_view.empty:
    st.info("현재 선택 조건에는 사고 다발지역 기록이 없습니다. 전체 사고 통계는 위 차트에서 계속 확인할 수 있습니다.")
else:
    map_center = {"lat": float(hotspot_view["위도"].mean()), "lon": float(hotspot_view["경도"].mean())}
    map_zoom = 11 if len(selected_districts) <= 3 else 10
    fig_map = px.scatter_map(
        hotspot_view,
        lat="위도", lon="경도", size="사고건수", color="사고건수",
        color_continuous_scale=[[0, "#FFD77F"], [0.5, "#F2984C"], [1, "#D94E59"]],
        size_max=17,
        hover_name="장소",
        hover_data={"연도": True, "자치구": True, "사고건수": True, "사상자수": True,
                    "위도": False, "경도": False, "사고다발지fid": False},
        zoom=map_zoom, center=map_center,
        height=540,
    )
    fig_map.update_layout(
        map_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="white", coloraxis_colorbar=dict(title="사고건수"),
        font=dict(family="Arial, Malgun Gothic, sans-serif", color=NAVY),
    )
    st.plotly_chart(fig_map, use_container_width=True)

st.markdown(
    '<div class="small-note">해석 주의: 사고 다발지역은 일정 기준에 따라 선정된 장소만 포함합니다. '
    '지도에 표시되지 않은 곳에서도 사고가 발생할 수 있고, 같은 장소가 여러 연도에 반복 기록될 수 있습니다.</div>',
    unsafe_allow_html=True,
)

# ────────── 11주차 4-1: 선택 조건의 표와 다운로드 ──────────
section("05", "데이터 확인과 다운로드", "그래프·지도에 사용한 것과 같은 선택 조건을 적용한 표를 확인할 수 있습니다.")
with st.expander("자치구별 사고 통계 원자료 확인", expanded=False):
    st.dataframe(view.sort_values(["연도", "자치구"]), hide_index=True, use_container_width=True)
    st.download_button(
        "현재 선택 조건: 전체 사고 통계 CSV 저장",
        data=view.to_csv(index=False).encode("utf-8-sig"),
        file_name="selected_district_accidents.csv", mime="text/csv",
    )
with st.expander("사고 다발지역 기록 원자료 확인", expanded=False):
    st.dataframe(hotspot_view.sort_values(["연도", "자치구"]), hide_index=True, use_container_width=True)
    st.download_button(
        "현재 선택 조건: 사고 다발지역 CSV 저장",
        data=hotspot_view.to_csv(index=False).encode("utf-8-sig"),
        file_name="selected_hotspots.csv", mime="text/csv",
    )

st.divider()
st.markdown("**데이터 출처와 분석 기준**")
st.markdown(
    "[한국도로교통공단 지자체별 대상사고 통계](https://opendata.koroad.or.kr/api/selectSttDataSet.do) · "
    "[한국도로교통공단 보행어린이 교통사고 다발지역 정보](https://opendata.koroad.or.kr/api/selectChildDataSet.do)"
)
st.caption(
    "전체 사고 통계는 '어린이보행사고' 분류를 사용했습니다. "
    "2010–2011년은 다발지역 자료가 없어 비교 가능한 2012–2025년을 공통 분석 범위로 사용합니다. "
    "분석 결과는 인과관계나 개별 지역의 위험도를 직접 증명하지 않습니다."
)
