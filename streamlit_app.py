import os
import datetime as dt
import requests
import streamlit as st

ATPT_OFCDC_SC_CODE = "B10"
SD_SCHUL_CODE = "7010194"

DEFAULT_KEY = "90f59dd0310f49d1b0a46d80b55770e6"
NEIS_KEY = os.getenv("NEIS_KEY", DEFAULT_KEY)

BASE_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"


def ymd(d):
    return d.strftime("%Y%m%d")


def fetch_meal(date_, meal_code):
    params = {
        "KEY": NEIS_KEY,
        "Type": "json",
        "ATPT_OFCDC_SC_CODE": ATPT_OFCDC_SC_CODE,
        "SD_SCHUL_CODE": SD_SCHUL_CODE,
        "MMEAL_SC_CODE": str(meal_code),
        "MLSV_YMD": ymd(date_),
    }

    try:
        r = requests.get(BASE_URL, params=params, timeout=10)
        data = r.json()

        rows = data["mealServiceDietInfo"][1]["row"]
        dish = rows[0]["DDISH_NM"]

        return dish.replace("<br/>", "\n")

    except:
        return "급식 없음 🙂"


st.set_page_config(page_title="급식", layout="centered")

st.markdown("""
<style>

/* 위젯 폭 */
.block-container {
    max-width:260px;
    padding-top:40px;
}

/* 컬럼 줄바꿈 금지 + 간격 제거 */
div[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap:0px !important;
}

/* 컬럼 폭 강제 축소 가능 */
div[data-testid="column"] {
    padding:0px !important;
    min-width:0 !important;
}

/* 버튼 스타일 */
.stButton button {
    width:100%;
    padding:2px 6px;
    font-size:12px;
    border-radius:6px;
}

/* 메뉴 */
.menu {
    white-space: pre-wrap;
    font-size:14px;
    line-height:1.6;
    margin-top:6px;
}

</style>
""", unsafe_allow_html=True)


if "meal_mode" not in st.session_state:
    st.session_state.meal_mode = 2


today = dt.date.today()

# 버튼
col1, col2 = st.columns(2, gap="small")

with col1:
    if st.button("중식"):
        st.session_state.meal_mode = 2

with col2:
    if st.button("석식"):
        st.session_state.meal_mode = 3


menu = fetch_meal(today, st.session_state.meal_mode)

st.markdown(
    f'<div class="menu">{menu}</div>',
    unsafe_allow_html=True
)
