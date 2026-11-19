from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="일본을 찾는 계절", layout="wide")
colors = {"한국": "#0C7381", "대만": "#AF5720", "미국": "#6451A3"}
seasons = ["봄", "여름", "가을", "겨울"]
source = "https://www.jnto.go.jp/statistics/data/visitors-statistics/"
st.title("일본을 찾는 계절")
st.write("한국인은 언제 일본을 가장 많이 방문할까? 대만·미국과 월별 흐름 및 계절 비중을 비교해 보세요.")
st.caption("2023–2025 · 일본정부관광국(JNTO) · 국적·지역별 방일 외객 · 단위 명(연인원)")

@st.cache_data
def load_data():
    data = pd.read_csv(Path(__file__).parent / "data" / "arrivals.csv")
    data["계절"] = data["월"].map({
        3: "봄", 4: "봄", 5: "봄", 6: "여름", 7: "여름", 8: "여름",
        9: "가을", 10: "가을", 11: "가을", 12: "겨울", 1: "겨울", 2: "겨울",
    })
    data["연월"] = pd.to_datetime(dict(year=data["연도"], month=data["월"], day=1))
    return data

data = load_data()
years = st.sidebar.multiselect("연도", [2023, 2024, 2025], default=[2023, 2024, 2025])
markets = st.sidebar.multiselect("국가·지역", list(colors), default=list(colors))
start, end = st.sidebar.slider("월 범위", 1, 12, (1, 12))
view = data.loc[data["연도"].isin(years) & data["시장"].isin(markets)
                & data["월"].between(start, end)].sort_values("연월")
if view.empty:
    st.warning("연도와 국가·지역을 각각 하나 이상 선택해 주세요.")
    st.stop()

# 선택 연도에서 같은 달을 합쳐, 가장 많은 방문이 기록된 달을 찾습니다.
monthly = view.groupby(["월", "시장"], as_index=False)["방문객"].sum()
by_month = monthly.groupby("월")["방문객"].sum()
peak = by_month.idxmax()
a, b, c = st.columns(3)
a.metric("선택 기간 방문객", f"{view['방문객'].sum():,}명")
b.metric("선택 시장 합산 최고 월", f"{peak}월")
c.metric(f"{peak}월 누적 방문객", f"{by_month.max():,}명")

st.subheader("방문 규모는 어떻게 변했을까?")
# 연도·월 필터에서 빠진 달은 빈칸으로 남겨 선이 이어지지 않게 합니다.
timeline = view.pivot(index="연월", columns="시장", values="방문객")
timeline = timeline.reindex(pd.date_range(view["연월"].min(), view["연월"].max(), freq="MS"))
timeline = timeline.rename_axis("연월").reset_index().melt("연월", value_name="방문객")
fig = px.line(timeline, x="연월", y="방문객", color="시장", markers=True,
              color_discrete_map=colors, labels={"방문객": "방문객 (명)"})
fig.update_yaxes(rangemode="tozero", tickformat=",")
st.plotly_chart(fig, width="stretch")

left, right = st.columns(2)
with left:
    st.subheader("어느 달에 방문이 몰렸을까?")
    st.caption("선택 연도의 같은 달끼리 합산한 방문객 수")
    fig = px.bar(monthly, x="월", y="방문객", color="시장", barmode="group",
                 color_discrete_map=colors, labels={"방문객": "누적 방문객 (명)"})
    fig.update_xaxes(dtick=1, ticksuffix="월")
    st.plotly_chart(fig, width="stretch")
with right:
    st.subheader("계절별 비중은 어떻게 다를까?")
    st.caption("분모는 각 시장의 선택 기간 총방문객. 월 범위를 줄이면 분모도 바뀝니다.")
    seasonal = view.groupby(["시장", "계절"], as_index=False)["방문객"].sum()
    totals = seasonal.groupby("시장")["방문객"].transform("sum")
    seasonal["비중"] = 100 * seasonal["방문객"] / totals
    fig = px.bar(seasonal, x="계절", y="비중", color="시장", barmode="group",
                 color_discrete_map=colors, category_orders={"계절": seasons},
                 labels={"비중": "선택 기간 내 비중 (%)"}, text_auto=".1f")
    fig.update_yaxes(ticksuffix="%", rangemode="tozero")
    st.plotly_chart(fig, width="stretch")

st.subheader("선택한 조건에서 읽는 결과")
for market in markets:
    months = monthly.loc[monthly["시장"] == market]
    best = months.loc[months["방문객"].idxmax()]
    groups = seasonal.loc[seasonal["시장"] == market]
    leading = groups.loc[groups["비중"].idxmax()]
    st.write(f"**{market}** · 누적 최고는 {best['월']}월({best['방문객']:,}명), "
             f"비중이 가장 높은 계절은 {leading['계절']}({leading['비중']:.1f}%)입니다.")
st.caption("봄 3–5월 · 여름 6–8월 · 가을 9–11월 · 겨울은 각 역년의 1·2·12월. 방문 목적 전체를 포함하며 반복 방문도 집계됩니다.")
with st.expander("관광 마케팅에 어떻게 활용할까?"):
    st.write("3년 전체에서 한국은 매년 12월, 미국은 매년 6월에 방문객이 가장 많았습니다. "
             "한국어 12월 여행 기획전과 미국 대상 6월 여행 상품을 후보로 두고, 예약일 자료로 홍보 시작 시점을 정해볼 수 있습니다. "
             "대만은 연도마다 최고 월이 달라 여름 세 달을 함께 검토할 만합니다.")
    st.write("이는 캠페인 가설입니다. 방문 통계만으로 방학·항공료의 영향이나 광고 효과를 알 수 없습니다. "
             "예약 전환율과 예약 한 건당 광고비를 비교해 검증해야 합니다.")
with st.expander("선택한 원자료와 출처"):
    table = view[["연도", "월", "시장", "계절", "방문객"]]
    st.dataframe(table, hide_index=True, width="stretch")
    st.download_button("선택한 데이터 CSV 저장", table.to_csv(index=False).encode("utf-8-sig"),
                       "selected_arrivals.csv", "text/csv")
    st.markdown(f"[일본정부관광국 국적·월별 방일 외객 통계]({source})")
    st.caption("2026-11-18 게시본. 월별 값 108개, 시장별·연도별 12개월 합계와 공식 누계 9건 일치.")
