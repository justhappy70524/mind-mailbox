from datetime import datetime
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="마음 우체통", page_icon="📮", layout="centered")

# --- CSS 스타일 및 애니메이션 ---
st.markdown(
    """
    <style>
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(15px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .title-container {
        animation: fadeInUp 0.8s ease-out;
        text-align: center;
        margin-bottom: 20px;
    }

    /* 버튼 스타일 */
    div.stButton > button {
        transition: all 0.3s ease !important;
        border-radius: 8px !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 5px 15px rgba(59, 130, 246, 0.4) !important;
    }

    /* 보관함 카드 스타일 */
    .mail-card {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 12px;
        border-left: 5px solid #3b82f6;
        color: white;
        transition: all 0.3s ease;
        animation: fadeInUp 0.5s ease-out;
    }
    .mail-card:hover {
        transform: translateX(5px) translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        border-left-color: #60a5fa;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 구글 시트 링크 및 웹 앱 URL 불러오기
try:
    SHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]
    WEBAPP_URL = st.secrets["connections"]["gsheets"]["webapp_url"]
except Exception:
    SHEET_URL = ""
    WEBAPP_URL = ""

# --- 상단 타이틀 (깔끔한 중앙 정렬) ---
st.markdown(
    """
    <div class="title-container">
        <h1>📮 오늘의 한마디 마음 우체통</h1>
        <p style="color: #94a3b8; font-size: 1.1rem;">오늘 하루 마음속에 담아둔 이야기가 있나요? 따뜻한 한마디를 남겨주세요.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- 마음 남기기 입력 폼 (학생들이 보게 되는 메인 화면) ---
with st.form("mail_form", clear_on_submit=True):
    nickname = st.text_input("닉네임 (비워두면 익명)", placeholder="따뜻한 사람")
    message = st.text_area(
        "오늘의 한마디", placeholder="오늘 하루도 정말 고생 많았어요!"
    )
    submitted = st.form_submit_button("마음 보내기 💌", use_container_width=True)

if submitted:
    if message.strip() == "":
        st.warning("한마디 내용을 입력해 주세요!")
    elif not WEBAPP_URL:
        st.error("웹 앱 URL(webapp_url) 설정이 누락되었습니다.")
    else:
        if nickname.strip() == "":
            nickname = "익명"

        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            payload = {"nickname": nickname, "message": message, "time": now_time}
            response = requests.post(WEBAPP_URL, json=payload)

            if response.status_code == 200:
                st.success("따뜻한 마음이 성공적으로 전달되었습니다! 🎈")
                st.balloons()
            else:
                st.error("전송에 실패했습니다. 다시 시도해 주세요.")
        except Exception as e:
            st.error(f"저장 중 오류 발생: {e}")

# --- 하단 관리자 전용 페이지 ---
st.markdown("<br><br>", unsafe_allow_html=True)
ADMIN_PASSWORD = "admin"  # 비밀번호 변경 필요 시 수정하세요

with st.expander("🔒 관리자 페이지 (비밀번호 필요)"):
    input_pw = st.text_input("관리자 비밀번호를 입력하세요", type="password")

    if input_pw == ADMIN_PASSWORD:
        st.success("관리자 인증되었습니다.")

        # 관리자 전용 새로고침 버튼
        if st.button("🔄 목록 새로고침"):
            st.rerun()

        st.subheader("📬 등록된 마음 보관함")

        try:
            csv_url = SHEET_URL.replace("/edit", "/export?format=csv")
            df = pd.read_csv(csv_url)
        except Exception:
            df = pd.DataFrame(columns=["닉네임", "한마디", "시간"])

        if df.empty or "한마디" not in df.columns or df["한마디"].dropna().empty:
            st.info("아직 등록된 마음이 없습니다.")
        else:
            for index, row in df.iloc[::-1].iterrows():
                nick = row.get("닉네임", "익명")
                msg = row.get("한마디", "")
                time_str = row.get("시간", "")

                if pd.notna(msg) and str(msg).strip() != "":
                    st.markdown(
                        f"""
                        <div class="mail-card">
                            <strong style="color: #60a5fa;">{nick}</strong>
                            <span style="font-size: 0.8rem; color: #94a3b8; float: right;">{time_str}</span>
                            <p style="margin-top: 8px; margin-bottom: 0; font-size: 1.05rem;">{msg}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
    elif input_pw != "":
        st.error("비밀번호가 올바르지 않습니다.")
