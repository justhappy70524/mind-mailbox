from datetime import datetime
import re
import time
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
    @keyframes smoothSlideDown {
        from {
            opacity: 0;
            transform: translateY(-10px);
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
    .admin-content {
        animation: smoothSlideDown 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }
    div.stButton > button {
        transition: all 0.3s ease !important;
        border-radius: 8px !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 5px 15px rgba(59, 130, 246, 0.4) !important;
    }
    .mail-card {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 12px;
        border-left: 5px solid #3b82f6;
        color: white;
        transition: all 0.3s ease;
        animation: fadeInUp 0.4s ease-out;
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

# --- 세션 상태(Session State) 초기화 ---
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "nick_input" not in st.session_state:
    st.session_state.nick_input = ""
if "msg_input" not in st.session_state:
    st.session_state.msg_input = ""
if "send_success" not in st.session_state:
    st.session_state.send_success = False
if "last_sent_time" not in st.session_state:
    st.session_state.last_sent_time = 0.0
if "clear_inputs" not in st.session_state:
    st.session_state.clear_inputs = False

if st.session_state.clear_inputs:
    st.session_state.nick_input = ""
    st.session_state.msg_input = ""
    st.session_state.clear_inputs = False


# --- 외부 파일 기반 금칙어 로드 및 검열 함수 ---
def load_bad_words():
    """bad_words.txt 파일에서만 금칙어를 읽어옵니다 (코드 내 하드코딩 없음)."""
    try:
        with open("bad_words.txt", "r", encoding="utf-8") as f:
            words = [line.strip() for line in f if line.strip()]
            return words
    except Exception:
        return []


def normalize_text(text):
    """띄어쓰기, 특수문자, 숫자, 이모티콘, 기호 우회를 완벽히 차단하기 위한 정규화"""
    text = text.lower()
    # 숫자(0-9) 및 특수문자, 공백을 모두 제거 (한글, 영문만 허용)
    text = re.sub(r'[^가-힣ㄱ-ㅎㅏ-ㅣa-z]', '', text)
    return text


def contains_profanity(text):
    """외부 파일의 금칙어 목록과 대조하여 포함 여부 확인"""
    bad_words = load_bad_words()
    if not bad_words:
        return False
        
    normalized = normalize_text(text)

    for word in bad_words:
        norm_word = normalize_text(word)
        if norm_word and norm_word in normalized:
            return True
    return False


# --- 설정 상수 ---
MAX_NICKNAME_LEN = 15
MAX_MESSAGE_LEN = 200
COOLDOWN_SECONDS = 10

# 구글 시트 링크 및 웹 앱 URL 불러오기
try:
    SHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]
    WEBAPP_URL = st.secrets["connections"]["gsheets"]["webapp_url"]
except Exception:
    SHEET_URL = ""
    WEBAPP_URL = ""

# --- 상단 타이틀 ---
st.markdown(
    """
    <div class="title-container">
        <h1>📮 오늘의 한마디 마음 우체통</h1>
        <p style="color: #94a3b8; font-size: 1.1rem;">오늘 하루 마음속에 담아둔 이야기가 있나요? 따뜻한 한마디를 남겨주세요.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- 마음 남기기 입력 폼 ---
with st.form("mail_form"):
    nickname = st.text_input(
        f"닉네임 (비워두면 익명, 최대 {MAX_NICKNAME_LEN}자)",
        placeholder="따뜻한 사람",
        max_chars=MAX_NICKNAME_LEN,
        key="nick_input",
    )
    message = st.text_area(
        f"오늘의 한마디 (최대 {MAX_MESSAGE_LEN}자)",
        placeholder="오늘 하루도 정말 고생 많았어요!",
        max_chars=MAX_MESSAGE_LEN,
        key="msg_input",
    )
    submitted = st.form_submit_button("마음 보내기 💌", use_container_width=True)

if st.session_state.send_success:
    st.success("따뜻한 마음이 성공적으로 전달되었습니다! 🎈")
    st.balloons()
    st.session_state.send_success = False

if submitted:
    current_time = time.time()
    elapsed = current_time - st.session_state.last_sent_time

    combined_text = f"{nickname} {message}"

    if elapsed < COOLDOWN_SECONDS:
        remain = int(COOLDOWN_SECONDS - elapsed) + 1
        st.warning(
            f"도배 방지를 위해 {remain}초 후에 다시 보낼 수 있습니다. 잠시만"
            " 기다려 주세요!"
        )
    elif message.strip() == "":
        st.warning("한마디 내용을 입력해 주세요!")
    elif len(message) > MAX_MESSAGE_LEN or len(nickname) > MAX_NICKNAME_LEN:
        st.warning("허용된 최대 글자 수를 초과했습니다.")
    elif contains_profanity(combined_text):
        st.error(
            "⚠️ 바르고 고운 말을 사용해 주세요! 부적절한 단어나 우회 표현이"
            " 감지되었습니다."
        )
    elif not WEBAPP_URL:
        st.error("웹 앱 URL(webapp_url) 설정이 누락되었습니다.")
    else:
        nick_to_send = nickname.strip() if nickname.strip() != "" else "익명"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        st.session_state.last_sent_time = time.time()

        try:
            payload = {
                "nickname": nick_to_send,
                "message": message.strip(),
                "time": now_str,
            }
            response = requests.post(WEBAPP_URL, json=payload)

            if response.status_code == 200:
                st.session_state.send_success = True
                st.session_state.clear_inputs = True
                st.rerun()
            else:
                st.session_state.last_sent_time = 0.0
                st.error("전송에 실패했습니다. 다시 시도해 주세요.")
        except Exception as e:
            st.session_state.last_sent_time = 0.0
            st.error(f"저장 중 오류 발생: {e}")

# --- 하단 관리자 페이지 ---
st.markdown("<br><br>", unsafe_allow_html=True)
ADMIN_PASSWORD = "admin"  # 비밀번호 변경 필요 시 수정

if not st.session_state.is_admin:
    with st.expander("🔒 관리자 페이지 (비밀번호 필요)"):
        with st.form("admin_login_form"):
            input_pw = st.text_input(
                "관리자 비밀번호를 입력하세요", type="password"
            )
            login_submitted = st.form_submit_button("로그인")

            if login_submitted:
                if input_pw == ADMIN_PASSWORD:
                    st.session_state.is_admin = True
                    st.session_state.current_page = 1
                    st.rerun()
                else:
                    st.error("비밀번호가 올바르지 않습니다.")
else:
    st.success("🔓 관리자 인증되었습니다.")

    if st.button("🔒 로그아웃", use_container_width=True):
        st.session_state.is_admin = False
        st.session_state.current_page = 1
        st.rerun()


    @st.fragment(run_every=2)
    def render_live_mailbox():
        st.markdown('<div class="admin-content">', unsafe_allow_html=True)
        st.subheader("📬 등록된 마음 보관함 (실시간 동기화 중 ⚡)")

        try:
            csv_url = SHEET_URL.replace("/edit", "/export?format=csv")
            df = pd.read_csv(csv_url)
        except Exception:
            df = pd.DataFrame(columns=["닉네임", "한마디", "시간"])

        if not df.empty and "한마디" in df.columns:
            valid_df = df[
                df["한마디"].notna()
                & (df["한마디"].astype(str).str.strip() != "")
            ].iloc[::-1]
        else:
            valid_df = pd.DataFrame()

        total_items = len(valid_df)

        if total_items == 0:
            st.info("아직 등록된 마음이 없습니다.")
        else:
            ITEMS_PER_PAGE = 20
            total_pages = (total_items - 1) // ITEMS_PER_PAGE + 1

            if st.session_state.current_page > total_pages:
                st.session_state.current_page = total_pages
            if st.session_state.current_page < 1:
                st.session_state.current_page = 1

            start_idx = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
            end_idx = start_idx + ITEMS_PER_PAGE
            page_items = valid_df.iloc[start_idx:end_idx]

            st.caption(
                f"총 {total_items}개의 마음 중 {start_idx + 1}~{min(end_idx, total_items)}개"
                f" 표시 중 (페이지 {st.session_state.current_page} /"
                f" {total_pages})"
            )

            for index, row in page_items.iterrows():
                nick = row.get("닉네임", "익명")
                msg = row.get("한마디", "")
                time_str = row.get("시간", "")

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

            if total_pages > 1:
                st.markdown("---")
                col1, col2, col3, col4, col5 = st.columns([1, 1, 1.5, 1, 1])

                with col1:
                    if st.button(
                        "⏮ 맨앞",
                        disabled=(st.session_state.current_page == 1),
                        use_container_width=True,
                        key="btn_first",
                    ):
                        st.session_state.current_page = 1

                with col2:
                    if st.button(
                        "◀ 이전",
                        disabled=(st.session_state.current_page == 1),
                        use_container_width=True,
                        key="btn_prev",
                    ):
                        st.session_state.current_page -= 1

                with col3:
                    st.markdown(
                        f"<h4 style='text-align: center; margin: 0; padding-top:"
                        f" 5px;'>{st.session_state.current_page} /"
                        f" {total_pages}</h4>",
                        unsafe_allow_html=True,
                    )

                with col4:
                    if st.button(
                        "다음 ▶",
                        disabled=(
                            st.session_state.current_page == total_pages
                        ),
                        use_container_width=True,
                        key="btn_next",
                    ):
                        st.session_state.current_page += 1

                with col5:
                    if st.button(
                        "맨뒤 ⏭",
                        disabled=(
                            st.session_state.current_page == total_pages
                        ),
                        use_container_width=True,
                        key="btn_last",
                    ):
                        st.session_state.current_page = total_pages

        st.markdown("</div>", unsafe_allow_html=True)


    render_live_mailbox()
