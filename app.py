import streamlit as st
from openai import OpenAI

# 페이지 기본 설정
st.set_page_config(
    page_title="25th 3rd 수니콘미션 챗GPT",
    page_icon="🤖",
    layout="wide"
)

# 스타일 추가
st.markdown("""
<style>
    /* 전체 컨테이너 */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1000px;
    }

    /* 메시지 컨테이너 스타일 */
    .stTextInput {
        border-radius: 15px;
    }
    
    /* 채팅 메시지 스타일 */
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.8rem;
        margin-bottom: 1.5rem;
        line-height: 1.8;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    /* 사용자 메시지 */
    .user-message {
        background-color: #f8f9fa;
        margin-left: 15%;
        border: 1px solid #e9ecef;
    }

    /* AI 메시지 */
    .ai-message {
        background-color: #ffffff;
        margin-right: 15%;
        border: 1px solid #e9ecef;
        font-size: 1.1rem;
    }

    /* 제목 스타일 */
    .main-title {
        text-align: center;
        color: #1a73e8;
        font-size: 2.2rem;
        font-weight: 600;
        margin-bottom: 2rem;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    /* 입력창 스타일 */
    .stChatInput {
        margin-top: 1rem;
        padding: 1rem;
        background: white;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    /* 사이드바 스타일 */
    .css-1d391kg {
        padding: 2rem 1rem;
    }

    /* 강조 텍스트 */
    .highlight {
        background-color: #e8f0fe;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
    }

    /* 목록 스타일 */
    .ai-message ul {
        margin: 1rem 0;
        padding-left: 1.5rem;
    }

    .ai-message li {
        margin: 0.5rem 0;
    }

    /* 섹션 제목 */
    .section-title {
        color: #1a73e8;
        font-size: 1.2rem;
        font-weight: 600;
        margin: 1.5rem 0 0.8rem;
        border-bottom: 2px solid #e8f0fe;
        padding-bottom: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 제목
st.markdown('<h1 class="main-title">25th 3rd 수니콘미션 챗GPT</h1>', unsafe_allow_html=True)

# 시스템 프롬프트 수정
SYSTEM_PROMPT = """당신은 전문적인 AI 어시스턴트입니다. 답변할 때:

1. 답변 구조:
   - 주요 내용을 섹션별로 구분하여 설명
   - 각 섹션은 '## 섹션명'으로 시작
   - 중요 정보는 **강조** 표시
   - 전문 용어는 `코드 블록`으로 표시

2. 포맷팅:
   - 깔끔한 글머리 기호로 목록 작성
   - 적절한 여백 유지
   - 표나 코드는 마크다운 형식으로 정리

3. 스타일:
   - 전문적이고 명확한 어조
   - PPT 형식의 구조화된 내용
   - 읽기 쉽게 단락 구분"""

# 사이드바 설정
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    model = st.selectbox(
        "모델 선택",
        ["GPT-4 (고성능)", "GPT-3.5 (빠른응답)"],
        format_func=lambda x: x.split(" ")[0]
    )
    st.markdown("---")
    st.markdown("### 📝 사용 방법")
    st.markdown("1. 원하는 모델을 선택하세요")
    st.markdown("2. 질문을 입력하세요")
    st.markdown("3. 엔터를 눌러 전송하세요")
    st.markdown("---")
    st.markdown("### 🎯 특징")
    st.markdown("• 전문적인 답변 제공")
    st.markdown("• PPT 스타일 포맷팅")
    st.markdown("• 실시간 스트리밍 응답")

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
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(f'<div class="user-message">{prompt}</div>', unsafe_allow_html=True)

    with st.chat_message("assistant", avatar="🤖"):
        model_name = "gpt-4" if "GPT-4" in model else "gpt-3.5-turbo"
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *st.session_state.messages
        ]

        stream = client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response}) 