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
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ────────── 디자인 설정 ──────────
NAVY = "#15324F"
TEAL = "#078A95"
ORANGE = "#EA8C50"
MUTED = "#66798F"
GRID = "#E7EEF5"
PAPER = "#FFFFFF"

st.markdown(
    """
    <style>
    :root {color-scheme: light;}
    .stApp {background: #F5F8FC; color: #18314D;}
    .block-container {max-width: 1430px; padding-top: 1.3rem; padding-bottom: 3.5rem;}
    [data-testid="stSidebar"] {background: #EEF4F9; border-right: 1px solid #DFE7F0;}
    [data-testid="stSidebar"] .block-container {padding-top: 1.8rem;}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {font-size: 0.9rem;}
    .hero {
        background: linear-gradient(110deg, #112D4A 0%, #214866 100%);
        color: white; border-radius: 21px; padding: 32px 38px 30px;
        margin-bottom: 17px; box-shadow: 0 10px 25px rgba(21,50,79,.12);
    }
    .hero .eyebrow {font-size: 11px; font-weight: 750; letter-spacing: 2px; color: #B4E5E9; margin-bottom: 10px;}
    .hero h1 {font-size: clamp(1.55rem, 2.7vw, 2.55rem); color: white; font-weight: 800;
              letter-spacing: -1.3px; margin: 0 0 11px; line-height: 1.3;}
    .hero h1 span {color: #88E0DA;}
    .hero p {font-size: 0.99rem; color: #E1EBF2; line-height: 1.65; margin: 0;}
    .hero .meta {margin-top: 19px; display: flex; flex-wrap: wrap; gap: 9px;}
    .hero .meta span {font-size: 0.77rem; border: 1px solid rgba(255,255,255,.27);
                      background: rgba(255,255,255,.08); border-radius: 24px; padding: 6px 11px; color: #EFF9FC;}
    div[data-testid="stMetric"] {background: white; border: 1px solid #E0E8F0; border-radius: 15px;
                                   padding: 17px 19px 14px; box-shadow: 0 2px 9px rgba(21,50,79,.025);}
    [data-testid="stMetricLabel"] {font-size: 0.85rem; color: #65798C; font-weight: 600;}
    [data-testid="stMetricValue"] {color: #123250; font-weight: 760; letter-spacing: -0.7px;}
    .section-head {margin: 25px 0 3px; display:flex; align-items:center; gap:10px;}
    .section-head .num {display:inline-flex; align-items:center; justify-content:center; width:26px; height:26px;
                       border-radius: 9px; background: #DDF1F3; color: #066B78; font-size: 0.81rem; font-weight: 800;}
    .section-head h2 {font-size: 1.19rem; letter-spacing: -.35px; color: #17334E; margin: 0; font-weight: 800;}
    .section-intro {font-size: 0.87rem; color: #6B7E91; margin: 0 0 13px;}
    .note {padding: 14px 17px; border-left: 3px solid #0F8995; background: #EAF4F6;
           border-radius: 0 12px 12px 0; font-size: .89rem; line-height: 1.7; color: #29465D;}
    .note b {color: #14536D;}
    .small-note {font-size: .81rem; color: #6E8193; margin: 6px 0 15px;}
    .sidebar-title {font-size: 1.08rem; font-weight: 800; color: #18364F; margin-bottom: 4px;}
    .sidebar-subtitle {font-size: .80rem; color: #6B7E91; line-height: 1.5; margin-bottom: 19px;}
    hr {border-color: #DFE7F0 !important;}
    @media (max-width: 700px) {
        .hero {padding: 23px 19px; border-radius: 16px;}
        .hero h1 {font-size: 1.42rem;}
        .block-container {padding-top: .7rem;}
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
      <div class="eyebrow">DATA STORY / SEOUL ROAD SAFETY</div>
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
        color_continuous_scale=[[0, "#6CCBCB"], [0.5, "#0A919E"], [1, "#18577D"]],
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
