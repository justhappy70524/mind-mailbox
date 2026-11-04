from datetime import datetime
import gspread
import pandas as pd
import streamlit as st

st.set_page_config(page_title="마음 우체통", page_icon="📮", layout="centered")

st.title("📮 오늘의 한마디 마음 우체통")
st.write("오늘 하루 마음속에 담아둔 이야기가 있나요? 따뜻한 한마디를 남겨주세요.")

# --- 구글 시트 데이터 불러오기 (gspread 이용) ---
SHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]


def get_sheet():
  # 서비스 계정이 없어도 Public 편집 가능 시트에 접근할 수 있도록 연동
  gc = gspread.public_authorize()
  sh = gc.open_by_url(SHEET_URL)
  return sh.get_worksheet(0)


try:
  # 판다스로 시트 데이터 실시간 읽기
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
  else:
    if nickname.strip() == "":
      nickname = "익명"

    now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
      # gspread를 이용해 구글 시트 맨 아래 줄에 직접 추가
      gc = gspread.public_authorize()
      sh = gc.open_by_url(SHEET_URL)
      worksheet = sh.get_worksheet(0)

      worksheet.append_row([nickname, message, now_time])

      st.success("따뜻한 마음이 성공적으로 전달되었습니다! 🎈")
      st.balloons()
      st.rerun()
    except Exception as e:
      st.error(f"저장 중 오류 발생: {e}")

# --- 다른 사람들의 마음 보관함 ---
st.markdown("---")
st.subheader("📬 다른 사람들의 마음 보관함")

if df.empty or "한마디" not in df.columns or df["한마디"].dropna().empty:
  st.info("아직 등록된 마음이 없습니다. 첫 번째 한마디의 주인공이 되어보세요!")
else:
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
