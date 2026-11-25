"""산업데이터시각화 개인 프로젝트 | 서울 어린이 보행 교통사고 분석

11주차: @st.cache_data → 사이드바 위젯 → 필터링 → 지표/Plotly → 표/CSV 저장
12주차: app.py 기준 상대 경로, GitHub + Streamlit Community Cloud 배포
"""
from pathlib import Path
import base64
import html

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
        box-shadow: 0 12px 29px rgba(14,44,73,.16);
        min-height: 296px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .hero h1, .hero p, .hero .meta, .hero .eyebrow {position: relative; z-index: 1;}
    .hero h1 {max-width: 680px; text-shadow: 0 1px 5px rgba(9,28,46,.32);}
    .hero p {max-width: 660px; text-shadow: 0 1px 3px rgba(9,28,46,.28);}
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
    .hero .meta span {backdrop-filter: blur(3px);}
    .insight-card {
        background: #FFFFFF; border: 1px solid #E6EBF2;
        border-top: 3px solid #FFC64A;
        border-radius: 13px; padding: 17px 19px 18px;
        min-height: 142px; box-shadow: 0 4px 14px rgba(20,47,75,.035);
        font-size: .91rem; line-height: 1.8; color: #46576B;
    }
    .insight-card.coral {border-top-color: #E65D62;}
    .insight-card.blue {border-top-color: #3186B8;}
    .insight-card .mini-title {
        display:block; font-weight:850; color:#1B344B;
        margin-bottom:6px; font-size:.99rem;
    }
    .insight-card b {color:#203B53;}
    .source-strip {
        border:1px solid #E5EAF1; border-radius:12px;
        padding:11px 16px; background:#ECF3FA;
        color:#5B7187; font-size:.81rem;
    }

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
        .hero {min-height: 275px; padding-top:23px;}
        .hero:after {
           content: ""; position:absolute; inset:0;
           background:linear-gradient(90deg, rgba(17,43,73,.15), rgba(17,43,73,.68));
           pointer-events:none;
        }
        .insight-card {min-height: auto;}
        .block-container {padding-top: .8rem;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

HERE = Path(__file__).parent

# 배포할 때 app.py와 hero_crosswalk.png를 같은 폴더에 올려야 합니다.
# 이미지가 없어도 분석 기능은 정상 작동하도록 기본 배경색을 유지합니다.
hero_image_path = HERE / "hero_crosswalk.png"
if hero_image_path.exists():
    encoded_hero = base64.b64encode(hero_image_path.read_bytes()).decode("ascii")
    st.markdown(
        '<style>.hero {'
        'background-image: linear-gradient(90deg, rgba(16,42,69,.99) 0%, '
        'rgba(16,42,69,.94) 37%, rgba(16,42,69,.66) 61%, '
        'rgba(16,42,69,.04) 90%), url("data:image/png;base64,' + encoded_hero + '");'
        'background-size: cover, cover; background-position: center, center 54%;'
        '}</style>',
        unsafe_allow_html=True,
    )



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
      <div class="eyebrow"><span class="safety-mark">🚸</span> DATA STORY / SEOUL ROAD SAFETY</div>
      <h1>서울 어린이 보행 교통사고<br><span>시공간 분석 대시보드</span></h1>
      <p>교통사고는 언제 줄었을까? 사고가 집중된 곳은 어디일까?<br>
      연도별 발생 추이와 사고 다발지역 분포를 두 가지 공공데이터로 살펴봅니다.</p>
      <div class="meta"><span>2012–2025년 공통 분석</span><span>서울 25개 자치구</span><span>한국도로교통공단 공개데이터</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)


# 탭으로 정보 구분: 기존 5개 시각화를 삭제하지 않고 각각의 분석 화면으로 이동
st.markdown("""
<style>
/* 명확한 선택 상태, 네이비/옐로/코랄의 교통안전 B안 유지 */
[data-baseweb="tab-list"] {
    background: #FFFFFF; border: 1px solid #E3E9F1;
    border-radius: 13px; padding: 6px 8px;
    gap: 5px; box-shadow: 0 3px 13px rgba(20,47,75,.045);
    margin: 8px 0 16px;
}
button[data-baseweb="tab"] {
    border-radius: 8px; padding: 10px 18px;
    color: #27425D; font-weight: 750; font-size: .92rem;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: #FFF0C5; color: #17324D;
}
[data-baseweb="tab-highlight"] { background: #E7A600 !important; height: 3px; }
[data-testid="stTabs"] [data-testid="stPlotlyChart"] { margin-bottom: 8px; }
.tab-explain {
    margin: 1px 0 14px; color: #536C83; font-size: .91rem;
    border-left: 4px solid #FFC64A; padding: 10px 14px;
    background: #FFF9ED; border-radius: 0 8px 8px 0;
}
@media (max-width: 850px) {
    button[data-baseweb="tab"] {font-size: .81rem; padding: 7px 9px;}
    .hero h1 {max-width: 100%;}
}
</style>
""", unsafe_allow_html=True)

# ────────── 11주차 2-3: 선택 조건 → 동일한 view로 모든 시각화 생성 ──────────
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
trend = (view.groupby("연도", as_index=False)[metric_label]
         .sum().sort_values("연도"))
hotspot_trend = (hotspot_view.groupby("연도").size()
                 .reindex(range(years[0], years[1]+1), fill_value=0)
                 .rename("기록 수").reset_index())
ranking = (view.groupby("자치구", as_index=False)[metric_label]
           .sum().sort_values([metric_label, "자치구"], ascending=[False, True]))
ranking_top = ranking.head(12).sort_values(metric_label, ascending=True)

# 히트맵도 막대·꺾은선·지도와 같은 view와 선택 지표를 사용한다.
matrix = (view.pivot_table(index="자치구", columns="연도", values=metric_label,
                           aggfunc="sum", fill_value=0)
          .reindex(index=sorted(selected_districts),
                   columns=list(range(years[0], years[1]+1)), fill_value=0))

st.markdown('<div class="section-head"><span class="num">01</span><h2>핵심 지표</h2></div>',
            unsafe_allow_html=True)
st.markdown('<div class="section-intro">사이드바에서 선택한 기간과 자치구를 기준으로 자동 집계합니다.</div>',
            unsafe_allow_html=True)
c1,c2,c3,c4 = st.columns(4, gap="medium")
c1.metric(f"선택 기간 {metric_label}", f"{view[metric_label].sum():,}{unit}")
if len(trend)>1 and trend[metric_label].iloc[0]>0:
    start_value=float(trend[metric_label].iloc[0]); end_value=float(trend[metric_label].iloc[-1])
    change=(end_value-start_value)/start_value*100
    c2.metric("첫해 대비 마지막해", f"{change:+.1f}%",
              help=f"{years[0]}년 {start_value:,.0f}{unit} → {years[1]}년 {end_value:,.0f}{unit}")
else:
    c2.metric("첫해 대비 마지막해", "—", help="한 해만 선택했거나 첫해 값이 0이면 변화율을 계산하지 않습니다.")
c3.metric("사고 다발지역 기록", f"{len(hotspot_view):,}개")
c4.metric("선택 자치구", f"{len(selected_districts):,}개")
st.caption("※ 다발지역 기록 수는 연도별 선정 기록의 합계로, 서로 다른 장소의 고유 개수가 아닙니다.")

# ────────── Plotly 공통 디자인 / 시각화 함수 ──────────
def style_figure(fig, height=370):
    fig.update_layout(height=height, paper_bgcolor=PAPER, plot_bgcolor=PAPER,
                      font=dict(family="Arial, Malgun Gothic, sans-serif", color=NAVY, size=12),
                      margin=dict(l=12,r=18,t=22,b=14),
                      hoverlabel=dict(bgcolor="white",font_size=13,font_color=NAVY),
                      showlegend=False)
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=GRID, tickfont=dict(color=MUTED))
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False,
                     rangemode="tozero", tickfont=dict(color=MUTED))
    return fig


def section(index, title, description):
    st.markdown(f'<div class="section-head"><span class="num">{index}</span><h2>{title}</h2></div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="section-intro">{description}</div>', unsafe_allow_html=True)


def create_trend_chart():
    fig=px.line(trend,x="연도",y=metric_label,markers=True,
                labels={"연도":"연도",metric_label:f"{metric_label} ({unit})"},
                color_discrete_sequence=[TEAL])
    fig.update_traces(line=dict(width=3.2),marker=dict(size=8,line=dict(color="white",width=1.4)),
                      hovertemplate=f"%{{x}}년<br>{metric_label}: %{{y:,.0f}}{unit}<extra></extra>")
    fig.update_xaxes(dtick=1)
    return style_figure(fig,400)


def create_hotspot_trend_chart():
    fig=px.line(hotspot_trend,x="연도",y="기록 수",markers=True,
                labels={"연도":"연도","기록 수":"다발지역 기록 수 (개)"},
                color_discrete_sequence=[ORANGE])
    fig.update_traces(line=dict(width=3.2),marker=dict(size=8,line=dict(color="white",width=1.4)),
                      hovertemplate="%{x}년<br>다발지역 기록: %{y:,.0f}개<extra></extra>")
    fig.update_xaxes(dtick=1)
    return style_figure(fig,400)


def create_ranking_chart():
    fig=px.bar(ranking_top,x=metric_label,y="자치구",orientation="h",text=metric_label,
               color_discrete_sequence=[TEAL],
               labels={metric_label:f"{metric_label} ({unit})","자치구":""})
    fig.update_traces(marker=dict(color=TEAL,line=dict(width=0)),
                      texttemplate="%{x:,.0f}",textposition="outside",cliponaxis=False,
                      hovertemplate=f"%{{y}}<br>{metric_label}: %{{x:,.0f}}{unit}<extra></extra>")
    style_figure(fig, height=475)
    fig.update_layout(margin=dict(l=10,r=55,t=12,b=15))
    fig.update_xaxes(showgrid=True,gridcolor=GRID,rangemode="tozero")
    fig.update_yaxes(showgrid=False,categoryorder="array",
                     categoryarray=ranking_top["자치구"].tolist())
    return fig


def create_heatmap_chart(show_numbers=False):
    # 값이 많은 자치구도 구분되도록 실수 사고건수 0부터 순차적 색상을 사용.
    color_scale=[[0.00,"#FFF8E8"],[0.33,"#FFD18C"],
                 [0.67,"#F58A68"],[1.00,"#BE3F4F"]]
    fig=px.imshow(matrix,aspect="auto",color_continuous_scale=color_scale,
                  labels={"x":"연도","y":"자치구","color":f"{metric_label} ({unit})"},
                  text_auto=",.0f" if show_numbers else False)
    fig.update_traces(hovertemplate=f"%{{y}} · %{{x}}년<br>{metric_label}: %{{z:,.0f}}{unit}<extra></extra>")
    fig.update_layout(height=max(330, min(870, 28*len(matrix)+135)),
                      paper_bgcolor="white",plot_bgcolor="white",
                      font=dict(family="Arial, Malgun Gothic, sans-serif",color=NAVY,size=12),
                      margin=dict(l=25,r=15,t=15,b=22),
                      coloraxis_colorbar=dict(title=unit,thickness=14))
    fig.update_xaxes(type="category",side="bottom",tickangle=0,
                     title_text="연도",tickfont=dict(size=11),showgrid=False)
    fig.update_yaxes(type="category",title_text="자치구",autorange="reversed",
                     tickfont=dict(size=11),showgrid=False,scaleanchor=None)
    return fig


def create_hotspot_map():
    center={"lat":float(hotspot_view["위도"].mean()),
            "lon":float(hotspot_view["경도"].mean())}
    zoom=11 if len(selected_districts)<=3 else 10
    fig=px.scatter_map(hotspot_view,lat="위도",lon="경도",
                       size="사고건수",color="사고건수",size_max=19,
                       color_continuous_scale=[[0,"#FFE2A0"],[.5,"#F39A55"],[1,"#D94E59"]],
                       hover_name="장소",
                       hover_data={"연도":True,"자치구":True,"사고건수":True,
                                   "사상자수":True,"위도":False,"경도":False,"사고다발지fid":False},
                       zoom=zoom,center=center,height=610)
    fig.update_layout(map_style="open-street-map",
                      margin=dict(l=0,r=0,t=0,b=0),paper_bgcolor="white",
                      coloraxis_colorbar=dict(title="사고건수"),
                      font=dict(family="Arial, Malgun Gothic, sans-serif",color=NAVY))
    return fig

# ────────── 네 개의 분석 화면: 공통 필터와 KPI는 항상 상단에 유지 ──────────
tab_trend,tab_region,tab_map,tab_insight=st.tabs([
    "📈 연도별 추이", "🌡️ 지역 비교 · 히트맵", "🗺️ 사고 다발지역 지도", "📋 결과 · 원자료"
])

with tab_trend:
    section("02","시간에 따른 변화","전체 사고 추이와 사고 다발지역으로 선정된 기록 수를 비교합니다.")
    left,right=st.columns(2,gap="large")
    with left:
        st.markdown(f"**연도별 {metric_label} 추이**")
        st.plotly_chart(create_trend_chart(),use_container_width=True,config={"displayModeBar":False})
    with right:
        st.markdown("**연도별 사고 다발지역 선정 기록 수**")
        st.plotly_chart(create_hotspot_trend_chart(),use_container_width=True,config={"displayModeBar":False})
    if len(trend)>1:
        change_pct=(trend[metric_label].iloc[-1]-trend[metric_label].iloc[0])/trend[metric_label].iloc[0]*100 if trend[metric_label].iloc[0]>0 else None
        change_str=f"{change_pct:+.1f}%" if change_pct is not None else "계산 불가"
        st.markdown(f'<div class="tab-explain"><b>기간 변화:</b> {years[0]}년에서 {years[1]}년까지 '
                    f'{metric_label}의 첫해 대비 마지막해 변화율은 <b>{change_str}</b>입니다. '
                    '이 추세만으로 사고 감소의 원인을 단정할 수 없습니다.</div>',unsafe_allow_html=True)
    else:
        st.info("한 해를 선택했습니다. 장기 추세를 비교하려면 연도 범위를 넓혀 보세요.")

with tab_region:
    section("03","자치구별 비교와 히트맵",
            "막대그래프는 선택 기간의 지역별 합계를, 히트맵은 자치구·연도별 값을 보여줍니다.")
    st.markdown(f"**자치구별 {metric_label} 비교 · 상위 12개**")
    st.plotly_chart(create_ranking_chart(),use_container_width=True,config={"displayModeBar":False})
    st.caption("가로 막대그래프에는 상위 12개 자치구만 표시합니다. 전체 자치구 통계는 '결과 · 원자료' 탭에서 확인할 수 있습니다.")
    st.markdown("**자치구 × 연도 히트맵**")
    st.markdown('<div class="tab-explain">각 칸의 색이 진할수록 선택한 지표의 값이 큽니다. '
                '히트맵은 <b>사고건수 등 절대적인 수치</b>의 비교이며, 어린이 1인당 위험도를 의미하지는 않습니다.</div>',
                unsafe_allow_html=True)
    show_heatmap_numbers=st.checkbox("히트맵 칸에 실제 수치 표시",value=False)
    st.plotly_chart(create_heatmap_chart(show_heatmap_numbers),use_container_width=True,
                    config={"displayModeBar":False})
    st.caption("행: 선택 자치구 · 열: 선택 연도 · 색: 선택 지표(사고건수/부상자수/사망자수). 마우스를 올리면 정확한 값을 확인할 수 있습니다.")

with tab_map:
    section("04","사고 다발지역 위치 지도",
            "교통사고가 여러 번 발생해 다발지역으로 선정된 곳의 대표 좌표를 표시합니다.")
    if hotspot_view.empty:
        st.info("현재 선택 조건에는 사고 다발지역 기록이 없습니다. 다른 연도나 자치구를 선택해 보세요.")
    else:
        st.plotly_chart(create_hotspot_map(),use_container_width=True,
                        config={"displayModeBar":True,"scrollZoom":False})
        st.caption("마커의 크기·색은 해당 기록의 사고건수에 비례합니다. 마우스를 올려 장소·연도·사고건수·사상자수를 확인하세요.")
        st.markdown("**선택 조건 내 사고 다발지역 기록 (사고건수 상위 10개)**")
        columns=["연도","자치구","장소","사고건수","사상자수"]
        st.dataframe(hotspot_view.sort_values(["사고건수","사상자수"],ascending=[False,False])
                     [columns].head(10),hide_index=True,use_container_width=True)
    st.markdown('<div class="tab-explain">이 지도는 <b>모든 사고 발생 지점</b>이 아니라 '
                '<b>사고 다발지역 선정 기록</b>만 표시합니다. 지도 밖 또는 마커가 없는 곳에서도 사고는 발생할 수 있습니다.</div>',
                unsafe_allow_html=True)

with tab_insight:
    section("05","주요 발견과 해석의 한계",
            "현재 선택 조건의 결과를 정리하고, 원본 CSV를 확인하거나 다운로드할 수 있습니다.")
    first_year=int(trend["연도"].iloc[0]); last_year=int(trend["연도"].iloc[-1])
    first_value=float(trend[metric_label].iloc[0]); last_value=float(trend[metric_label].iloc[-1])
    if first_year==last_year:
        change_text=f"{first_year}년 {metric_label}은 <b>{last_value:,.0f}{unit}</b>입니다."
    elif first_value>0:
        pct=(last_value-first_value)/first_value*100
        change_text=(f"<b>{first_year}년 {first_value:,.0f}{unit}</b> → "
                     f"<b>{last_year}년 {last_value:,.0f}{unit}</b> (<b>{pct:+.1f}%</b>)")
    else:
        change_text=f"<b>{first_year}년 {first_value:,.0f}{unit}</b> → <b>{last_year}년 {last_value:,.0f}{unit}</b>"
    highest=ranking.iloc[0]
    name=html.escape(str(highest["자치구"]))
    one,two,three=st.columns(3,gap="medium")
    with one:
        st.markdown(f'<div class="insight-card coral"><span class="mini-title">📉 기간별 변화</span>'
                    f'{change_text}<br><small>연도별 변동은 한 방향으로만 일어나지 않을 수 있습니다.</small></div>',
                    unsafe_allow_html=True)
    with two:
        st.markdown(f'<div class="insight-card"><span class="mini-title">📍 지역 비교</span>'
                    f'선택 기간의 {metric_label} 합계가 가장 큰 자치구는 '
                    f'<b>{name} ({highest[metric_label]:,.0f}{unit})</b>입니다.<br>'
                    '<small>어린이 인구·보행량 차이는 반영하지 않았습니다.</small></div>',
                    unsafe_allow_html=True)
    with three:
        st.markdown(f'<div class="insight-card blue"><span class="mini-title">⚠️ 해석 시 유의</span>'
                    f'사고 다발지역 <b>{len(hotspot_view):,}개</b>는 연도별 선정 기록 합계입니다.<br>'
                    '<small>전체 사고 위치나 고유 장소 수가 아닙니다.</small></div>',
                    unsafe_allow_html=True)

    st.markdown("### 그래프 검산 및 CSV 다운로드")
    with st.expander("자치구별 전체 사고 통계",expanded=False):
        st.dataframe(view.sort_values(["연도","자치구"]),hide_index=True,use_container_width=True)
        st.download_button("현재 선택 조건: 자치구 사고 통계 CSV 저장",
                           data=view.to_csv(index=False).encode("utf-8-sig"),
                           file_name="selected_district_accidents.csv",mime="text/csv")
    with st.expander("사고 다발지역 기록",expanded=False):
        st.dataframe(hotspot_view.sort_values(["연도","자치구"]),hide_index=True,use_container_width=True)
        st.download_button("현재 선택 조건: 사고 다발지역 CSV 저장",
                           data=hotspot_view.to_csv(index=False).encode("utf-8-sig"),
                           file_name="selected_hotspots.csv",mime="text/csv")
    st.markdown('<div class="source-strip">🚸 <b>해석 기준</b> · '
                '2012–2025년 공통 분석 기간 · 어린이 보행 교통사고 · '
                '연도·지역 필터는 그래프와 지도에 공통 적용</div>',
                unsafe_allow_html=True)
    st.markdown("**출처**")
    st.markdown("[한국도로교통공단 지자체별 대상사고 통계](https://opendata.koroad.or.kr/api/selectSttDataSet.do) · "
                "[한국도로교통공단 보행어린이 사고 다발지역](https://opendata.koroad.or.kr/api/selectChildDataSet.do)")
    st.caption("전체 사고 통계에서 '어린이보행사고'만 사용했습니다. "
               "2010~2011년은 사고 다발지역 데이터가 없어 비교 가능한 2012~2025년으로 제한했습니다. "
               "이번 분석은 인과관계나 자치구별 보행 위험도를 직접 증명하지 않습니다.")
