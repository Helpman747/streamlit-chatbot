import streamlit as st
from openai import OpenAI
from googleapiclient.discovery import build
import os

# 페이지 기본 설정
st.set_page_config(
    page_title="25th 3rd 수니콘미션 챗GPT",
    page_icon="🤖",
    layout="centered"
)

# CSS 스타일 직접 포함
st.markdown("""
<style>
/* 헤더 스타일 */
.header-banner {
    width: 100%;
    background: #1a1a1a;
    padding: 1rem 0;
    position: sticky;
    top: 0;
    z-index: 100;
}

.header-content {
    max-width: 800px;
    margin: 0 auto;
    text-align: center;
}

.header-image {
    max-width: 800px;  /* 컨테이너 너비에 맞춤 */
    width: 100%;
    height: auto;
    display: block;
}

/* 전체 페이지 배경 */
.stApp {
    background: #f7f7f8;
}

/* 전체 컨테이너 */
.main .block-container {
    max-width: 800px !important;
    margin: 0 auto !important;
    padding: 0 !important;
    background: white;
    min-height: 100vh;
    border-radius: 0;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
    padding-top: 0 !important;  /* 헤더 아래 패딩 제거 */
}

/* 제목 */
h1 {
    font-size: 1.5rem !important;
    padding: 1rem;
    border-bottom: 1px solid #e5e5e5;
    margin: 0 !important;
}

/* 메시지 영역 */
.messages-container {
    padding: 0;
    margin-bottom: 100px;  /* 입력창 높이만큼 여백 */
}

/* 메시지 스타일 */
.chat-message {
    padding: 1.5rem 2rem;
    line-height: 1.6;
    border-bottom: 1px solid #e5e5e5;
    margin: 0;
}

/* 사용자 메시지 */
.user-message {
    background: #f7f7f8;
}

/* AI 메시지 */
.assistant-message {
    background: white;
}

/* 입력창 영역 */
.input-area {
    position: fixed;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 800px;
    background: white;
    border-top: 1px solid #e5e5e5;
    padding: 1.5rem;
}

/* 입력창 스타일 */
.stChatInput {
    max-width: 768px !important;  /* 여백 고려 */
    margin: 0 auto !important;
}

/* 사이드바 */
.css-1d391kg {
    background: white;
    padding: 1rem;
}

/* 스크롤바 스타일 */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}
</style>

<!-- 헤더 배너 추가 -->
<div class="header-banner">
    <div class="header-content">
        <img src="배너이미지주소" alt="25th 3rd 수니콘미션" class="header-image">
    </div>
</div>
""", unsafe_allow_html=True)

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 제목 제거 (이미 컨테이너 안에 포함될 것이므로)
# st.markdown('<h1 class="main-title">25th 3rd 수니콘미션 챗GPT</h1>', unsafe_allow_html=True)

# 시스템 프롬프트 수정
SYSTEM_PROMPT = """당신은 음악에 대한 깊은 지식을 가진 친근한 AI 어시스턴트입니다. 답변할 때 다음 사항을 지켜주세요:

1. 음악 정보 제공
   - 곡의 장르, 스타일, 분위기를 자세히 설명
   - 아티스트의 음악적 특징과 이력 소개
   - 음악 제작 배경이나 뒷이야기 공유
   - 관련된 다른 곡이나 아티스트 추천

2. 답변 스타일
   - 친근하고 공감적인 대화체 사용
   - 음악 용어는 쉽게 풀어서 설명
   - 중요한 내용은 **강조**하여 표시
   - 🎵 🎸 🎹 등 관련 이모지 활용

3. 상세 분석
   - 가사의 의미와 메시지 해석
   - 음악적 구성과 특징 설명
   - 대중문화적 영향과 의의
   - 차트 성적이나 수상 이력

4. 추가 정보
   - 라이브 공연이나 뮤직비디오 언급
   - 팬덤 문화나 관련 이슈 소개
   - 최신 활동이나 향후 계획
   - 관련 플레이리스트나 믹스 추천"""

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
                f"💡 {item['title']}\n"
                f"📝 {item['snippet']}\n"
                f"🔗 참고: {item['link']}"
                for item in result["items"]
            ])
            return f"### 관련 검색 결과\n\n{search_results}"
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

# 제목 부분 제거 (상단 배너로 대체)
# st.markdown('<h1 style="text-align: center; padding: 1rem;">25th 3rd 수니콘미션 챗GPT</h1>', unsafe_allow_html=True)

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
    # 사용자 메시지 추가
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
            "content": search_results
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

    # 응답 저장
    st.session_state.messages.append({"role": "assistant", "content": response})

st.markdown('</div>', unsafe_allow_html=True)

# 채팅 컨테이너 종료
st.markdown('</div>', unsafe_allow_html=True)
