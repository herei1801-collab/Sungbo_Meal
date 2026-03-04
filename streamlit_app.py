import os
import datetime as dt
import requests
import streamlit as st


# =========================
# Config
# =========================
ATPT_OFCDC_SC_CODE = "B10"      # 서울특별시교육청
SD_SCHUL_CODE = "7010194"       # 성보고등학교

# 환경변수 NEIS_KEY가 있으면 그걸 우선 사용, 없으면 아래 기본값 사용
DEFAULT_KEY = "90f59dd0310f49d1b0a46d80b55770e6"
NEIS_KEY = os.getenv("NEIS_KEY", DEFAULT_KEY)

BASE_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"


# =========================
# Helpers
# =========================
def ymd(d: dt.date) -> str:
    return d.strftime("%Y%m%d")


def fetch_meal(date_: dt.date, meal_code: int) -> tuple[str | None, str | None]:
    """
    meal_code: 2=중식, 3=석식
    return: (menu_text or None, error_message or None)
    """
    params = {
        "KEY": NEIS_KEY,
        "Type": "json",
        "pIndex": 1,
        "pSize": 10,
        "ATPT_OFCDC_SC_CODE": ATPT_OFCDC_SC_CODE,
        "SD_SCHUL_CODE": SD_SCHUL_CODE,
        "MMEAL_SC_CODE": str(meal_code),
        "MLSV_YMD": ymd(date_),
    }

    try:
        r = requests.get(BASE_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return None, f"네트워크/요청 오류: {e}"

    # 정상 응답이면 mealServiceDietInfo가 있고, [0]=head, [1]=row 형태가 흔함
    # 데이터 없으면 RESULT 메시지만 오기도 함
    if "mealServiceDietInfo" not in data:
        # RESULT 기반 메시지 처리
        result = data.get("RESULT")
        if result and isinstance(result, dict):
            code = result.get("CODE", "")
            msg = result.get("MESSAGE", "데이터가 없습니다.")
            return None, f"{code} {msg}".strip()
        return None, "급식 데이터가 없습니다."

    try:
        rows = data["mealServiceDietInfo"][1].get("row", [])
        if not rows:
            return None, "급식 없음"
        dish = rows[0].get("DDISH_NM", "")
        if not dish:
            return None, "급식 없음"
        # <br/> 줄바꿈만 처리 (알레르기 번호는 그대로 유지)
        dish = dish.replace("<br/>", "\n").replace("<br />", "\n")
        return dish.strip(), None
    except Exception:
        return None, "응답 파싱 실패"


# =========================
# UI
# =========================
st.set_page_config(
    page_title="성보고 급식",
    page_icon="🍱",
    layout="centered",
)

# 위젯 느낌 CSS (카드형)
st.markdown(
    """
    <style>
      .block-container { max-width: 420px; padding-top: 16px; }
      .meal-card {
        border: 1px solid rgba(0,0,0,0.08);
        border-radius: 18px;
        padding: 16px 16px 12px 16px;
        background: rgba(255,255,255,0.88);
        box-shadow: 0 10px 30px rgba(0,0,0,0.06);
      }
      .title-row {
        display:flex; justify-content:space-between; align-items:center;
        margin-bottom: 8px;
      }
      .title {
        font-weight: 700; font-size: 16px;
      }
      .date {
        font-size: 12px; opacity: 0.7;
      }
      .subtitle {
        font-size: 12px; opacity: 0.7; margin-top: 10px;
      }
      .menu {
        white-space: pre-wrap;
        font-size: 14px;
        line-height: 1.55;
        margin-top: 10px;
      }
      .pill {
        display:inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        border: 1px solid rgba(0,0,0,0.10);
        background: rgba(245,245,245,0.8);
        font-size: 12px;
        margin-right: 6px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# 상태 유지: 기본 중식
if "meal_mode" not in st.session_state:
    st.session_state.meal_mode = 2  # 2=중식, 3=석식

today = dt.date.today()

st.markdown(
    f"""
    <div class="meal-card">
      <div class="title-row">
        <div class="title">🍱 성보고 급식</div>
        <div class="date">{today.strftime("%Y.%m.%d (%a)")}</div>
      </div>
    """,
    unsafe_allow_html=True,
)

# 날짜 선택(공지 목적이면 오늘 고정도 가능하지만, 편의로 남김)
picked = st.date_input("날짜", value=today, label_visibility="collapsed")

col1, col2 = st.columns(2)
with col1:
    if st.button("중식 ☀️", use_container_width=True):
        st.session_state.meal_mode = 2
with col2:
    if st.button("석식 🌙", use_container_width=True):
        st.session_state.meal_mode = 3

mode_label = "중식 ☀️" if st.session_state.meal_mode == 2 else "석식 🌙"
st.markdown(f'<span class="pill">{mode_label}</span>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">오늘의 메뉴</div>', unsafe_allow_html=True)

menu, err = fetch_meal(picked, st.session_state.meal_mode)

if menu:
    st.markdown(f'<div class="menu">{menu}</div>', unsafe_allow_html=True)
else:
    # err가 “급식 없음”이면 깔끔하게, 아니면 오류 메시지 노출
    if err and "급식 없음" not in err:
        st.markdown(f'<div class="menu">급식 없음 🙂\n\n(참고: {err})</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="menu">급식 없음 🙂</div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# 하단 작은 정보
with st.expander("설정/디버그", expanded=False):
    st.write("ATPT_OFCDC_SC_CODE:", ATPT_OFCDC_SC_CODE)
    st.write("SD_SCHUL_CODE:", SD_SCHUL_CODE)
    st.write("KEY 사용 방식: 환경변수 NEIS_KEY가 있으면 우선 사용 / 없으면 코드 기본값 사용")
    st.caption("공지 목적이면 이 앱을 Edge 앱 모드로 설치하고 PowerToys Always on Top(Win+Ctrl+T)로 위젯처럼 고정하면 편해.")
