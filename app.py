import streamlit as st
from openai import OpenAI

# 페이지 기본 설정
st.set_page_config(
    page_title="AI 채팅",
    page_icon="🤖",
    layout="wide"
)

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 제목
st.title("AI 채팅 서비스")

# 사이드바에 모델 선택 옵션
model = st.sidebar.selectbox(
    "모델 선택",
    ["gpt-4", "gpt-3.5-turbo"]
)

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 메시지 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력 처리
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 응답 생성
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response}) 