from datetime import datetime
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="마음 우체통", page_icon="📮", layout="centered")

# --- CSS 애니메이션 효과 추가 ---
st.markdown(
    """
    <style>
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .main-title { animation: fadeInUp 0.8s ease-out; }
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
        animation: fadeInUp 0.5s ease-out;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "<h1 class='main-title'>📮 오늘의 한마디 마음 우체통</h1>",
    unsafe_allow_html=True,
)
st.write("오늘 하루 마음속에 담아둔 이야기가 있나요? 따뜻한 한마디를 남겨주세요.")

# 세션 상태에 내가 보낸 메시지 목록 저장 공간 초기화
if "my_messages" not in st.session_state:
  st.session_state.my_messages = []

# 구글 시트 링크 및 웹 앱 URL 불러오기
try:
  SHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]
  WEBAPP_URL = st.secrets["connections"]["gsheets"]["webapp_url"]
except Exception:
  st.error(
      "Settings > Secrets에 spreadsheet와 webapp_url이 올바르게 설정되었는지"
      " 확인해 주세요!"
  )
  SHEET_URL = ""
  WEBAPP_URL = ""

# --- 마음 남기기 입력 폼 ---
with st.form("mail_form", clear_on_submit=True):
  nickname = st.text_input("닉네임 (비워두면 익명)", placeholder="따뜻한 사람")
  message = st.text_area(
      "오늘의 한마디", placeholder="오늘 하루도 정말 고생 많았어요!"
  )
  submitted = st.form_submit_button("마음 보내기 💌")

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
        # 내 세션 기록에 추가 (수정을 위해 기억해둠)
        st.session_state.my_messages.append(
            {"nickname": nickname, "message": message, "time": now_time}
        )
      else:
        st.error("전송에 실패했습니다. 다시 시도해 주세요.")
    except Exception as e:
      st.error(f"저장 중 오류 발생: {e}")

# --- 내가 보낸 마음 관리 영역 (본인 화면에만 보임) ---
if st.session_state.my_messages:
  st.markdown("---")
  st.subheader("📝 내가 방금 보낸 마음 (여기서 수정 가능해요)")

  for idx, item in enumerate(st.session_state.my_messages):
    with st.expander(
        f"[{item['time']}] {item['nickname']}님의 마음 수정하기"
    ):
      new_nick = st.text_input("닉네임 수정", item["nickname"], key=f"nick_{idx}")
      new_msg = st.text_area(
          "내용 수정", item["message"], key=f"msg_{idx}"
      )

      col1, col2 = st.columns(2)
      with col1:
        if st.button("수정 내용 전송 💾", key=f"update_{idx}"):
          # 수정된 내용을 구글 시트에 다시 전송
          update_payload = {
              "nickname": new_nick,
              "message": new_msg + " (수정됨)",
              "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          }
          res = requests.post(WEBAPP_URL, json=update_payload)
          if res.status_code == 200:
            st.session_state.my_messages[idx]["nickname"] = new_nick
            st.session_state.my_messages[idx]["message"] = new_msg
            st.success("성공적으로 수정 반영되었습니다! ✨")
            st.rerun()
          else:
            st.error("수정 전송 실패")
      with col2:
        if st.button("목록에서 내리기 🗑️", key=f"del_{idx}"):
          st.session_state.my_messages.pop(idx)
          st.success("내 화면에서 삭제되었습니다.")
          st.rerun()

# --- 관리자 전용 영역 ---
st.markdown("---")

ADMIN_PASSWORD = "admin"  # 관리자 비밀번호 (필요시 변경)

with st.expander("🔒 관리자 페이지 (비밀번호 필요)"):
  input_pw = st.text_input("관리자 비밀번호를 입력하세요", type="password")

  if input_pw == ADMIN_PASSWORD:
    st.success("관리자 인증되었습니다.")
    st.subheader("📬 전체 등록된 마음 보관함")

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
