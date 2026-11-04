import json
import os
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="마음 우체통", page_icon="📮", layout="centered"
)

st.title("📮 오늘의 한마디 마음 우체통")
st.write("오늘 하루 마음속에 담아둔 이야기가 있나요? 따뜻한 한마디를 남겨주세요.")

# 메시지를 저장할 파일 이름
DATA_FILE = "messages.json"


# 기존 메시지 불러오기 함수
def load_messages():
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  return []


# 메시지 저장하기 함수
def save_messages(messages):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(messages, f, ensure_ascii=False, indent=4)


messages = load_messages()

# 입력 폼 만들기
with st.form("message_form"):
  nickname = st.text_input("닉네임 (비워두면 익명)", placeholder="따뜻한 사람")
  content = st.text_input(
      "오늘의 한마디", placeholder="오늘 하루도 정말 고생 많았어요!"
  )
  submit_button = st.form_submit_button(label="마음 보내기 💌")

  if submit_button:
    if content.strip() == "":
      st.warning("메시지 내용을 입력해주세요!")
    else:
      new_msg = {"nickname": nickname if nickname else "익명", "content": content}
      messages.insert(0, new_msg)  # 최신 글이 위로 오도록 추가
      save_messages(messages)
      st.success("소중한 마음이 우체통에 안전하게 전달되었습니다! 💛")
      st.rerun()

st.divider()

# 다른 사람들의 메시지 보여주기
st.subheader("📬 다른 사람들의 마음 보관함")
if not messages:
  st.info("아직 등록된 마음이 없어요. 첫 번째 한마디의 주인공이 되어보세요!")
else:
  for msg in messages:
    st.info(f"**{msg['nickname']}**: {msg['content']}")
