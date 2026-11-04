from datetime import datetime
import pandas as pd
import streamlit as st

# 페이지 설정
st.set_page_config(page_title="마음 우체통", page_icon="📮", layout="centered")

st.title("📮 오늘의 한마디 마음 우체통")
st.write("오늘 하루 마음속에 담아둔 이야기가 있나요? 따뜻한 한마디를 남겨주세요.")

# 구글 시트 연결 (Streamlit GsheetsConnection 활용)
try:
    conn = st.connection("gsheets", type="gsheets")
    # 시트에서 기존 데이터 불러오기 (캐시 없이 실시간 로드)
    df = conn.read(ttl=0)
except Exception as e:
    st.error("구글 시트 연결 설정이 아직 완료되지 않았거나 형식이 올바르지 않습니다. 아래 설정 방법을 확인해 주세요!")
    df = pd.DataFrame(columns=["닉네임", "한마디", "시간"])

# --- 마음 남기기 입력 폼 ---
with st.form("mail_form", clear_on_submit=True):
    nickname = st.text_input("닉네임 (비워두면 익명)", placeholder="따뜻한 사람")
    message = st.text_area("오늘의 한마디", placeholder="오늘 하루도 정말 고생 많았어요!")
    submitted = st.form_submit_button("마음 보내기 💌")

    if submitted:
        if message.strip() == "":
            st.warning("한마디 내용을 입력해 주세요!")
        else:
            # 닉네임이 비어있으면 '익명'으로 처리
            if nickname.strip() == "":
                nickname = "익명"

            # 현재 시간 기록
            now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 새로운 데이터 행 생성
            new_data = pd.DataFrame([{"닉네임": nickname, "한마디": message, "시간": now_time}])

            try:
                # 기존 데이터에 새로운 데이터 합치기
                updated_df = pd.concat([df, new_data], ignore_index=True)
                # 구글 시트에 업데이트 반영
                conn.update(data=updated_df)
                st.success("따뜻한 마음이 성공적으로 전달되었습니다! 🎈")
                st.balloons()
                # 화면 즉시 새로고침
                st.rerun()
            except Exception as e:
                st.error(f"데이터를 저장하는 중 문제가 발생했습니다. ({e})")

# --- 다른 사람들의 마음 보관함 ---
st.markdown("---")
st.subheader("📬 다른 사람들의 마음 보관함")

if df.empty or "한마디" not in df.columns or df["한마디"].count() == 0:
    st.info("아직 등록된 마음이 없습니다. 첫 번째 한마디의 주인공이 되어보세요!")
else:
    # 최신글이 위로 오도록 역순 정렬
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
