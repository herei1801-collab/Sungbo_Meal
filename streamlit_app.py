import os
import datetime as dt
import requests
import streamlit as st

# =========================
# Config
# =========================
ATPT_OFCDC_SC_CODE = "B10"      # 서울특별시교육청
SD_SCHUL_CODE = "7010194"       # 성보고등학교

DEFAULT_KEY = "90f59dd0310f49d1b0a46d80b55770e6"
NEIS_KEY = os.getenv("NEIS_KEY", DEFAULT_KEY)

BASE_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"


def ymd(d: dt.date) -> str:
    return d.strftime("%Y%m%d")


def fetch_meal(date_: dt.date, meal_code: int) -> tuple[str | None, str | None]:
    params = {
        "KEY": NEIS_KEY,
        "Type": "json",
        "pIndex": 1,
        "pSize": 10,
        "ATPT_OFCDC_SC_CODE": ATPT_OFCDC_SC_CODE,
        "SD_SCHUL_CODE": SD_SCHUL_CODE,
        "MMEAL_SC_CODE": str(meal_code),  # 2=중식, 3=석식
        "MLSV_YMD": ymd(date_),
    }

    try:
        r = requests.get(BASE_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return None, f"네트워크/요청 오류: {e}"

    if "mealServiceDietInfo" not in data:
        result = data.get("RESULT")
        if isinstance(result, dict):
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
        dish = dish.replace("<br/>", "\n").replace("<br />", "\n")
        return dish.strip(), None
    except Exception:
        return None, "응답 파싱 실패"


# =========================
# UI
# =========================
st.set_page_config(page_title="성보고 급식", page_icon="🍱", layout="centered")

# 위젯용: 상단 잘림 방지 + 여백 압축 + 버튼/컨트롤 타이트
st.markdown(
    """
    <style>
      /* 전체 폭/여백: 위젯(작은 창)에서 잘림 방지 */
      .block-container {
        max-width: 420px;
        padding-top: 50px;       /* 기존보다 위 여백 줄임 */
        padding-bottom: 10px;
      }

      /* Streamlit 기본 header(상단) 여백 줄이기 */
      header[data-testid="stHeader"] { height: 0px; }
      div[data-testid="stToolbar"] { visibility: hidden; height: 0px; }

      .meal-card {
        border: 1px solid rgba(0,0,0,0.08);
        border-radius: 18px;
        padding: 14px 14px 12px 14px;
        background: rgba(255,255,255,0.88);
        box-shadow: 0 10px 30px rgba(0,0,0,0.06);
      }

      .title-row {
        display:flex;
        justify-content:space-between;
        align-items:center;
        margin-bottom: 10px;
      }

      .title {
        font-weight: 700;
        font-size: 16px;
      }

      .date {
        font-size: 12px;
        opacity: 0.7;
      }

      /* 메뉴 텍스트 */
      .menu {
        white-space: pre-wrap;
        font-size: 14px;
        line-height: 1.6;
        margin-top: 10px;
      }

      /* 버튼 아래 여백 조금 줄이기 */
      div[data-testid="column"] > div { padding-top: 0px; }
      .stButton button { padding: 0.55rem 0.75rem; border-radius: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# 기본 상태: 중식
if "meal_mode" not in st.session_state:
    st.session_state.meal_mode = 2  # 2=중식, 3=석식

today = dt.date.today()

# 카드 헤더(상단 날짜는 카드 오른쪽에만 표시 / 아래 date_input 제거)
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

# ✅ 날짜 입력 제거 (오늘 고정)
picked = today

# ✅ 버튼만 남기기
col1, col2 = st.columns(2)
with col1:
    if st.button("중식 ☀️", use_container_width=True):
        st.session_state.meal_mode = 2
with col2:
    if st.button("석식 🌙", use_container_width=True):
        st.session_state.meal_mode = 3

# ✅ 버튼 밑의 “중식” pill 제거
# ✅ “오늘의 메뉴” 문구 제거

menu, err = fetch_meal(picked, st.session_state.meal_mode)

if menu:
    st.markdown(f'<div class="menu">{menu}</div>', unsafe_allow_html=True)
else:
    # 에러 메시지는 너무 길면 보기 싫으니, 위젯용으로는 깔끔하게 처리
    st.markdown('<div class="menu">급식 없음 🙂</div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ✅ 설정/디버그는 접어두고, 필요 없으면 아래 블록 통째로 삭제해도 됨
with st.expander("설정/디버그", expanded=False):
    st.write("ATPT_OFCDC_SC_CODE:", ATPT_OFCDC_SC_CODE)
    st.write("SD_SCHUL_CODE:", SD_SCHUL_CODE)
    st.caption("창을 더 작게 쓰면 Edge 앱 모드 + PowerToys Always on Top(Win+Ctrl+T) 조합이 편함.")
