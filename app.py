﻿import streamlit as st
from openai import OpenAI
from googleapiclient.discovery import build

# 페이지 기본 설정
st.set_page_config(
    page_title="25th 3rd 수니콘미션 챗GPT",
    page_icon="🤖",
    layout="wide"
)

# 스타일 수정
st.markdown("""
<style>
    /* 전체 페이지 배경 */
    .stApp {
        background: #f0f2f5;
    }

    /* 메인 컨테이너 */
    .main .block-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        min-height: 100vh;
    }

    /* 메시지 스타일 */
    .chat-message {
        padding: 1.5rem 2rem;
        line-height: 1.6;
        border-bottom: 1px solid #f0f0f0;
    }

    /* 사용자 메시지 */
    .user-message {
        background: #f7f7f8;
    }

    /* AI 메시지 */
    .assistant-message {
        background: white;
    }

    /* 입력창 스타일 */
    .stChatInput {
        max-width: 800px !important;
        margin: 0 auto;
    }

    /* 사이드바 스타일 */
    .css-1d391kg {
        background: white;
        padding: 2rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 제목 제거 (이미 컨테이너 안에 포함될 것이므로)
# st.markdown('<h1 class="main-title">25th 3rd 수니콘미션 챗GPT</h1>', unsafe_allow_html=True)

# 시스템 프롬프트 수정
SYSTEM_PROMPT = """당신은 최신 트렌드와 정보를 잘 아는 AI 어시스턴트입니다. 답변할 때:

1. 답변 구조:
   - 최신 트렌드와 현재 상황을 중심으로 설명
   - 각 섹션은 '## 섹션명'으로 시작
   - 중요한 최신 정보는 **강조**로 표시
   - 현재 상황과 미래 전망을 포함

2. 정보 제공:
   - 가장 최근의 트렌드와 변화를 중심으로 설명
   - 현재 진행 중인 변화나 발전 사항 포함
   - 미래 전망이나 예측도 함께 제시
   - 실제 사례나 구체적인 예시 포함

3. 스타일:
   - 전문적이고 명확한 어조
   - PPT 형식의 구조화된 내용
   - 읽기 쉽게 단락 구분"""

# Google 검색 함수 수정
def google_search(query, num_results=3):
    try:
        service = build("customsearch", "v1", developerKey=st.secrets["GOOGLE_API_KEY"])
        result = service.cse().list(
            q=query,
            cx=st.secrets["GOOGLE_CSE_ID"],
            num=num_results
        ).execute()

        if "items" in result:
            search_results = "\n\n".join([
                f"제목: {item['title']}\n내용: {item['snippet']}\n출처: {item['link']}"
                for item in result["items"]
            ])
            return search_results
        return ""
    except Exception as e:
        return ""

# 사이드바 설정
with st.sidebar:
    st.markdown("### ⚙️ 모델 설정")
    model = st.selectbox(
        "모델 선택",
        ["GPT-4 (고성능)", "GPT-3.5 (빠른응답)"],
        format_func=lambda x: x.split(" ")[0]
    )
    
    st.markdown("---")
    st.markdown("### 💬 대화 기록")
    
    # 대화 기록이 있는 경우 표시
    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        for idx, msg in enumerate(st.session_state.messages[-5:]):
            if msg["role"] == "user":
                st.markdown(f"{msg['content'][:30]}...")
    else:
        st.markdown("아직 대화 기록이 없습니다.")
    
    # 기록 초기화 버튼
    if st.button("대화 기록 초기화"):
        st.session_state.messages = []
        st.experimental_rerun()

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "안녕하세요! 무엇을 도와드릴까요?"
        }
    ]

# 채팅 컨테이너 시작
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# 컨테이너 제목 추가
st.markdown('<h1 style="text-align: center; padding: 1rem;">25th 3rd 수니콘미션 챗GPT</h1>', unsafe_allow_html=True)

# 메시지 영역 시작
st.markdown('<div class="messages-container">', unsafe_allow_html=True)

# 메시지 표시
for message in st.session_state.messages:
    st.markdown(
        f'<div class="{message["role"]}-message chat-message">{message["content"]}</div>',
        unsafe_allow_html=True
    )

# 메시지 영역 종료
st.markdown('</div>', unsafe_allow_html=True)

# 입력 영역
st.markdown('<div class="input-area">', unsafe_allow_html=True)
if prompt := st.chat_input("메시지를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # AI 응답 생성 및 처리
    search_results = google_search(prompt)
    model_name = "gpt-4" if "GPT-4" in model else "gpt-3.5-turbo"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *st.session_state.messages
    ]
    
    if search_results:
        messages.append({
            "role": "system",
            "content": f"다음은 이 질문에 대한 최신 검색 결과입니다. 이를 참고하여 최신 정보를 포함해 답변해주세요:\n\n{search_results}"
        })

    # 응답 생성
    message_placeholder = st.empty()
    response = ""
    
    for chunk in client.chat.completions.create(
        model=model_name,
        messages=messages,
        stream=True,
    ):
        if chunk.choices[0].delta.content is not None:
            response += chunk.choices[0].delta.content
            message_placeholder.markdown(
                f'<div class="assistant-message chat-message">{response}</div>',
                unsafe_allow_html=True
            )

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.experimental_rerun()

st.markdown('</div>', unsafe_allow_html=True)

# 채팅 컨테이너 종료
st.markdown('</div>', unsafe_allow_html=True)
