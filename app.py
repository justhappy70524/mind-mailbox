from datetime import datetime
import gspread
import pandas as pd
import streamlit as st

# 페이지 설정
st.set_page_config(page_title="마음 우체통", page_icon="📮", layout="centered")

st.title("📮 오늘의 한마디 마음 우체통")
st.write("오늘 하루 마음속에 담아둔 이야기가 있나요? 따뜻한 한마디를 남겨주세요.")


# 구글 시트 연결 함수 (Secrets 활용)
@st.cache_resource
def init_connection():
  # Streamlit Secrets에서 구글 시트 주소 가져오기
  sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
  gc = gspread.service_account_from_dict(
      st.secrets["gcp_service_account"]
  )  # 혹은 gspread 표준 인증 방식
  return sheet_url


# 데이터를 불러오고 저장하는 안전한 로직
try:
  sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]

  # gspread 인증 (Secrets에 서비스 계정 키가 있는 경우 또는 퍼블릭 시트 접근)
  # 만약 서비스 계정 설정이 복잡하다면 st.secrets 설정에 맞춰 구동됩니다.
  import json

  if "gcp_service_account" in st.secrets:
    gc = gspread.service_account_from_dict(
        dict(st.secrets["gcp_service_account"])
    )
    sh = gc.open_by_url(sheet_url)
    worksheet = sh.get_worksheet(0)
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
  else:
    # 서비스 계정 설정이 안 되어 있을 경우 안내
    st.error(
        "Streamlit Secrets에 gcp_service_account(구글 서비스 계정 인증 정보)"
        " 설정이 필요합니다."
    )
    df = pd.DataFrame(columns=["닉네임", "한마디", "시간"])
except Exception as e:
  # 만약 위 방식이 복잡하거나 시트가 비어있을 경우를 대비한 안전망
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
      # 구글 시트에 직접 행 추가하기
      if "gcp_service_account" in st.secrets:
        gc = gspread.service_account_from_dict(
            dict(st.secrets["gcp_service_account"])
        )
        sh = gc.open_by_url(
            st.secrets["connections"]["gsheets"]["spreadsheet"]
        )
        worksheet = sh.get_worksheet(0)
        worksheet.append_row([nickname, message, now_time])

      st.success("따뜻한 마음이 성공적으로 전달되었습니다! 🎈")
      st.balloons()
      st.rerun()
    except Exception as e:
      st.error(f"데이터를 저장하는 중 문제가 발생했습니다: {e}")

# --- 다른 사람들의 마음 보관함 ---
st.markdown("---")
st.subheader("📬 다른 사람들의 마음 보관함")

if df.empty or "한마디" not in df.columns or len(df) == 0:
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
