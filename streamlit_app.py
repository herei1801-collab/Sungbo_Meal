import os
import datetime as dt
import requests
import streamlit as st

ATPT_OFCDC_SC_CODE = "B10"
SD_SCHUL_CODE = "7010194"

DEFAULT_KEY = "90f59dd0310f49d1b0a46d80b55770e6"
NEIS_KEY = os.getenv("NEIS_KEY", DEFAULT_KEY)

BASE_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"


def ymd(d: dt.date) -> str:
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
        dish = dish.replace("<br/>", "\n")

        return dish

    except:
        return "급식 없음 🙂"


st.set_page_config(page_title="급식", page_icon="logo.png", layout="centered")

st.markdown("""
<style>

.block-container {
    max-width: 300px;
    padding-top: 50px;
}

/* 버튼 영역 */
.button-row {
    display:flex;
    gap:6px;
}

/* 버튼 작게 */
.stButton button {
    padding:2px 8px;
    font-size:13px;
    border-radius:8px;
}

/* 메뉴 */
.menu {
    white-space: pre-wrap;
    font-size:14px;
    line-height:1.6;
    margin-top:8px;
}

</style>
""", unsafe_allow_html=True)


if "meal_mode" not in st.session_state:
    st.session_state.meal_mode = 2


today = dt.date.today()


# 버튼 (붙어서 나란히)
col1, col2 = st.columns([1,1], gap="None")

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
