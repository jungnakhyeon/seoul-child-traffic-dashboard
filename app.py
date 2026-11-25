        hovertemplate="%{x}년<br>다발지역 기록: %{y:,.0f}개<extra></extra>",
    )
    fig_hotspot.update_xaxes(dtick=1)
    style_figure(fig_hotspot)
    st.plotly_chart(fig_hotspot, use_container_width=True, config={"displayModeBar": False})

section("03", "지역 비교와 공간 분포", "선택한 기간의 자치구별 지표와 사고 다발지역의 위치를 나란히 살펴봅니다.")
rank_col, map_col = st.columns([1, 1.1], gap="large")

with rank_col:
    st.markdown(f"**자치구별 {metric_label} 비교 · 상위 12개**")
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
    style_figure(fig_rank, height=465)
    fig_rank.update_layout(margin=dict(l=10, r=48, t=12, b=15))
    fig_rank.update_xaxes(showgrid=True, gridcolor=GRID, rangemode="tozero")
    fig_rank.update_yaxes(showgrid=False, categoryorder="array", categoryarray=ranking_top["자치구"].tolist())
    st.plotly_chart(fig_rank, use_container_width=True, config={"displayModeBar": False})
    st.caption("상위 12개만 표시하며, 전체 25개 자치구의 값은 아래 원자료 표에 있습니다.")

with map_col:
    st.markdown("**사고 다발지역 위치 지도**")
    if hotspot_view.empty:
        st.info("이 조건에는 사고 다발지역 기록이 없습니다. 다른 기간이나 자치구를 선택해 보세요.")
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
            height=465,
        )
        fig_map.update_layout(
            map_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="white", coloraxis_colorbar=dict(title="사고건수"),
            font=dict(family="Arial, Malgun Gothic, sans-serif", color=NAVY),
        )
        st.plotly_chart(fig_map, use_container_width=True)
    st.caption("마커 크기는 선정 기록별 사고건수에 비례하며, 마커를 가리키면 세부 정보를 확인할 수 있습니다.")

section("04", "핵심 해석과 데이터의 한계", "분석 결과를 사실에 근거해 해석하고, 단정할 수 없는 내용은 구분합니다.")
first_year = int(trend["연도"].iloc[0])
last_year = int(trend["연도"].iloc[-1])
first_value = float(trend[metric_label].iloc[0])
last_value = float(trend[metric_label].iloc[-1])
if first_year == last_year:
    change_text = f"{first_year}년의 {metric_label}은 <b>{last_value:,.0f}{unit}</b>입니다."
elif first_value > 0:
    pct = (last_value - first_value) / first_value * 100
    change_text = (
        f"<b>{first_year}년 {first_value:,.0f}{unit}</b> → "
        f"<b>{last_year}년 {last_value:,.0f}{unit}</b> "
        f"(<b>{pct:+.1f}%</b>)"
    )
else:
    change_text = f"<b>{first_year}년 {first_value:,.0f}{unit}</b> → <b>{last_year}년 {last_value:,.0f}{unit}</b>"

highest = ranking.iloc[0]
name = html.escape(str(highest["자치구"]))
col_insight1, col_insight2, col_insight3 = st.columns(3, gap="medium")
with col_insight1:
    st.markdown(
        f'<div class="insight-card coral"><span class="mini-title">📉 기간별 변화</span>'
        f'{change_text}<br><small>연도별 변동은 한 방향으로만 일어나지 않을 수 있습니다.</small></div>',
        unsafe_allow_html=True,
    )
with col_insight2:
    st.markdown(
        f'<div class="insight-card"><span class="mini-title">📍 지역 비교</span>'
        f'선택한 기간의 {metric_label} 합계가 가장 큰 자치구는 '
        f'<b>{name} ({highest[metric_label]:,.0f}{unit})</b>입니다.<br>'
        f'<small>단, 인구·보행량 차이는 반영하지 않았습니다.</small></div>',
        unsafe_allow_html=True,
    )
with col_insight3:
    st.markdown(
        f'<div class="insight-card blue"><span class="mini-title">⚠️ 해석 시 유의</span>'
        f'사고 다발지역 <b>{len(hotspot_view):,}개</b>는 연도별 선정 기록의 합입니다.<br>'
        f'<small>전체 사고 위치나 고유 장소 수가 아니며 사고 원인을 입증하지 않습니다.</small></div>',
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
st.markdown('<div class="source-strip">🚸  <b>분석 기준 안내</b> · 어린이 보행 교통사고 / 2012~2025년 공통 분석 기간 / 수치와 지도는 동일한 선택 조건 적용</div>', unsafe_allow_html=True)
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
