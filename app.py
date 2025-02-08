import streamlit as st
from openai import OpenAI

# 페이지 기본 설정
st.set_page_config(
    page_title="AI 채팅",
    page_icon="🤖",
    layout="wide"
)

# 스타일 추가
st.markdown("""
<style>
    /* 메시지 컨테이너 스타일 */
    .stTextInput {
        border-radius: 10px;
    }
    
    /* 채팅 메시지 스타일 */
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* 사용자 메시지 */
    .user-message {
        background-color: #f3f4f6;
        margin-left: 20%;
    }

    /* AI 메시지 */
    .ai-message {
        background-color: #ffffff;
        margin-right: 20%;
        border: 1px solid #e5e7eb;
    }

    /* 제목 스타일 */
    .main-title {
        text-align: center;
        color: #2563eb;
        font-size: 2.5rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 제목
st.markdown('<h1 class="main-title">AI 채팅 서비스</h1>', unsafe_allow_html=True)

# 사이드바 설정
with st.sidebar:
    st.image("https://your-logo-url.png", width=200)
    st.markdown("### 설정")
    model = st.selectbox(
        "모델 선택",
        ["GPT-4 (고성능)", "GPT-3.5 (빠른응답)"],
        format_func=lambda x: x.split(" ")[0]
    )
    st.markdown("---")
    st.markdown("### 사용 방법")
    st.markdown("1. 모델을 선택하세요")
    st.markdown("2. 메시지를 입력하세요")
    st.markdown("3. 엔터를 눌러 전송하세요")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 메시지 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"], 
        avatar="🧑‍💻" if message["role"] == "user" else "🤖"):
        st.markdown(f'<div class="{message["role"]}-message">{message["content"]}</div>', 
            unsafe_allow_html=True)

# 사용자 입력 처리
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(f'<div class="user-message">{prompt}</div>', unsafe_allow_html=True)

    # AI 응답 생성
    with st.chat_message("assistant", avatar="🤖"):
        model_name = "gpt-4" if "GPT-4" in model else "gpt-3.5-turbo"
        stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response}) 