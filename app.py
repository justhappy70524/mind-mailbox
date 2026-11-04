from datetime import datetime
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="마음 우체통", page_icon="📮", layout="centered")

st.title("📮 오늘의 한마디 마음 우체통")
st.write("오늘 하루 마음속에 담아둔 이야기가 있나요? 따뜻한 한마디를 남겨주세요.")

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

# 구글 시트 데이터를 CSV로 읽어와 화면에 표시
try:
  csv_url = SHEET_URL.replace("/edit", "/export?format=csv")
  df = pd.read_csv(csv_url)
except Exception:
  df = pd.DataFrame(columns=["닉네임", "한마디", "시간"])

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
      # 앱스 스크립트 웹 앱으로 데이터 전송 (쓰기)
      payload = {"nickname": nickname, "message": message, "time": now_time}
      response = requests.post(WEBAPP_URL, json=payload)

      if response.status_code == 200:
        st.success("따뜻한 마음이 성공적으로 전달되었습니다! 🎈")
        st.balloons()
        st.rerun()
      else:
        st.error("전송에 실패했습니다. 다시 시도해 주세요.")
    except Exception as e:
      st.error(f"저장 중 오류 발생: {e}")

# --- 다른 사람들의 마음 보관함 ---
st.markdown("---")
st.subheader("📬 다른 사람들의 마음 보관함")

if df.empty or "한마디" not in df.columns or df["한마디"].dropna().empty:
  st.info("아직 등록된 마음이 없습니다. 첫 번째 한마디의 주인공이 되어보세요!")
else:
  # 최신 글이 위로 오도록 역순 정렬
  for index, row in df.iloc[::-1].iterrows():
    nick = row.get("닉네임", "익명")
    msg = row.get("한마디", "")
    time_str = row.get("시간", "")

    if pd.notna(msg) and str(msg).strip() != "":
      with st.container():
        st.markdown(
            f"""
                    <div style="background-color: #1e293b; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #3b82f6; color: white;">
                        <strong style="color: #60a5fa;">{nick}</strong>
                        <span style="font-size: 0.8rem; color: #94a3b8; float: right;">{time_str}</span>
                        <p style="margin-top: 8px; margin-bottom: 0; font-size: 1.05rem;">{msg}</p>
                    </div>
                    """,
            unsafe_allow_html=True,
        )
