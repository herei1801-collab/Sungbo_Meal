import os
import datetime as dt
import requests
import streamlit as st
from zoneinfo import ZoneInfo  # Python 3.9+

ATPT_OFCDC_SC_CODE = "B10"
SD_SCHUL_CODE = "7010194"

DEFAULT_KEY = "90f59dd0310f49d1b0a46d80b55770e6"
NEIS_KEY = os.getenv("NEIS_KEY", DEFAULT_KEY)

BASE_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"

def ymd(d: dt.date) -> str:
    return d.strftime("%Y%m%d")

def today_kst() -> dt.date:
    return dt.datetime.now(ZoneInfo("Asia/Seoul")).date()

def fetch_meal(date_: dt.date, meal_code: int) -> str:
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

        # 급식 없는 날이면 키가 없거나 구조가 달라서 KeyError가 날 수 있음
        rows = data["mealServiceDietInfo"][1]["row"]
        dish = rows[0]["DDISH_NM"]
        return dish.replace("<br/>", "\n")

    except Exception:
        return "급식 없음 🙂"

st.set_page_config(page_title="급식", layout="centered")

# ✅ (선택) 자동 새로고침: 5분마다 화면 갱신
# - 밤새 켜두는 "위젯" 용도면 강추
st.autorefresh = getattr(st, "autorefresh", None)
if st.autorefresh:
    st.autorefresh(interval=5 * 60 * 1000, key="meal_refresh")  # 5분

st.markdown("""
<style>
.block-container { max-width:260px; padding-top:50px; }
div[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap:0px !important; }
div[data-testid="column"] { padding:0px !important; min-width:0 !important; }
.stButton button { width:100%; padding:2px 6px; font-size:12px; border-radius:6px; }
.menu { white-space: pre-wrap; font-size:14px; line-height:1.6; margin-top:6px; }
</style>
""", unsafe_allow_html=True)

if "meal_mode" not in st.session_state:
    st.session_state.meal_mode = 2  # 기본 중식

# ✅ KST 기준 오늘 날짜
today = today_kst()

col1, col2 = st.columns(2, gap="small")
with col1:
    if st.button("중식"):
        st.session_state.meal_mode = 2
with col2:
    if st.button("석식"):
        st.session_state.meal_mode = 3

menu = fetch_meal(today, st.session_state.meal_mode)
st.markdown(f'<div class="menu">{menu}</div>', unsafe_allow_html=True)
