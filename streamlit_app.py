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

st.markdown(
    """
    <style>
      /* 전체 폭/여백: 위젯(작은 창)에서 잘림 방지 */
      .block-container {
        max-width: 420px;
        padding-top: 50px;
        padding-bottom: 10px;
      }

      /* Streamlit 기본 header(상단) 여백 줄이기 */
      header[data-testid="stHeader"] { height: 0px; }
      div[data-testid="stToolbar"] { visibility: hidden; height: 0px; }

      /* ✅ 카드 전체를 다크 톤으로 (버튼 톤과 맞추기) */
      .meal-card {
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 18px;
        padding: 14px 14px 12px 14px;
        background: white;   /* 핵심: 상단 헤더도 같은 배경이 됨 */
      }

      .title-row {
        display:flex;
        justify-content:space-between;
        align-items:center;
        margin-bottom: 0px; /* 아래 간격은 btn-gap로 제어 */
      }

      .title {
        font-weight: 700;
        font-size: 16px;
        color: rgba(18, 20, 24, 0.92);
      }

      .date {
        font-size: 12px;
        color: rgba(18, 20, 24, 0.92);
      }

      /* ✅ 헤더-버튼 사이 간격 */
      .btn-gap { height: 10px; }  /* 여기 숫자만 키우면 더 벌어짐 */

      /* 메뉴 텍스트 */
      .menu {
        white-space: pre-wrap;
        font-size: 14px;
        line-height: 1.6;
        margin-top: 10px;
        color: rgba(255,255,255,0.90);
      }

      /* 버튼/컬럼 여백 */
      div[data-testid="column"] > div { padding-top: 0px; }

      /* 버튼 모양 */
      .stButton button {
        padding: 0.55rem 0.75rem;
        border-radius: 12px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# 기본 상태: 중식
if "meal_mode" not in st.session_state:
    st.session_state.meal_mode = 2  # 2=중식, 3=석식

today = dt.date.today()

# 카드 시작
st.markdown(
    f"""
    <div class="meal-card">
      <div class="title-row">
        <div class="title">🍱 성보고 급식</div>
        <div class="date">{today.strftime("%Y.%m.%d (%a)")}</div>
      </div>
      <div class="btn-gap"></div>
    """,
    unsafe_allow_html=True,
)

picked = today

# 버튼
col1, col2 = st.columns(2)
with col1:
    if st.button("중식 ☀️", use_container_width=True):
        st.session_state.meal_mode = 2
with col2:
    if st.button("석식 🌙", use_container_width=True):
        st.session_state.meal_mode = 3

menu, err = fetch_meal(picked, st.session_state.meal_mode)

if menu:
    st.markdown(f'<div class="menu">{menu}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="menu">급식 없음 🙂</div>', unsafe_allow_html=True)

# 카드 끝
st.markdown("</div>", unsafe_allow_html=True)

# (원하면 아래 expander는 삭제 가능)
with st.expander("설정/디버그", expanded=False):
    st.write("ATPT_OFCDC_SC_CODE:", ATPT_OFCDC_SC_CODE)
    st.write("SD_SCHUL_CODE:", SD_SCHUL_CODE)
    st.caption("창을 더 작게 쓰면 Edge 앱 모드 + PowerToys Always on Top(Win+Ctrl+T) 조합이 편함.")
