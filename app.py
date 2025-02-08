import streamlit as st
from openai import OpenAI
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import json  # 디버깅용 추가

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
SYSTEM_PROMPT = """당신은 친근하고 전문적인 AI 어시스턴트입니다. 답변할 때 다음 사항을 지켜주세요:

1. 답변 스타일
   - 친근하고 자연스러운 대화체 사용
   - 전문 용어는 쉽게 풀어서 설명
   - 중요한 내용은 **강조**하여 표시
   - 필요한 경우 이모지 활용

2. 답변 구조
   - 핵심 내용을 먼저 간단히 요약
   - 상세 설명은 단계별로 구분하여 제시
   - 예시나 비유를 통해 이해하기 쉽게 설명
   - 긴 내용은 적절히 문단 구분

3. 정보 제공
   - 최신 트렌드와 현재 상황 중심으로 설명
   - 신뢰할 수 있는 정보 인용
   - 다양한 관점에서 균형잡힌 정보 제공
   - 실용적인 조언이나 팁 포함

4. 특별 지침
   - 음악 관련 질문에는 더욱 전문적으로 답변
     * 곡의 장르, 스타일, 분위기 상세 설명
     * 아티스트의 음악적 특징과 이력 소개
     * 음악 제작 배경이나 뒷이야기 공유
     * 관련 곡이나 아티스트 추천

5. 마무리
   - 추가 질문이 있는지 확인
   - 필요한 경우 관련 주제 제안
   - 실천 가능한 다음 단계 제시"""

# Google API 연결 테스트
def test_google_api():
    try:
        service = build("customsearch", "v1", developerKey=st.secrets["GOOGLE_API_KEY"])
        test_result = service.cse().list(
            q="test",
            cx=st.secrets["GOOGLE_CSE_ID"],
            num=1
        ).execute()
        return "Google API 연결 성공"
    except Exception as e:
        return f"Google API 연결 실패: {str(e)}"

# 시작할 때 API 테스트 실행
print(test_google_api())

# Google 검색 함수 수정
def google_search(query, num_results=5):
    try:
        print(f"검색 시작: {query}")
        print(f"API 키: {st.secrets['GOOGLE_API_KEY'][:10]}...")
        print(f"검색 엔진 ID: {st.secrets['GOOGLE_CSE_ID']}")
        
        # 검색어 처리
        search_query = query  # 사이트 제한 없이 먼저 테스트
        
        service = build("customsearch", "v1", developerKey=st.secrets["GOOGLE_API_KEY"])
        
        try:
            result = service.cse().list(
                q=search_query,
                cx=st.secrets["GOOGLE_CSE_ID"],
                num=num_results,
                lr='lang_ko',
                gl='kr'
            ).execute()
            
            print(f"API 응답: {result.keys()}")
            print(f"검색 결과: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if "items" in result:
                search_results = []
                for item in result["items"]:
                    search_results.append(
                        f"제목: {item['title']}\n"
                        f"내용: {item['snippet']}\n"
                        f"출처: {item['link']}"
                    )
                return "\n\n".join(search_results)
            else:
                print("검색 결과 없음")
                return ""
                
        except Exception as api_error:
            print(f"API 호출 오류: {str(api_error)}")
            import traceback
            print(traceback.format_exc())
            return ""
            
    except Exception as e:
        print(f"전체 오류: {str(e)}")
        import traceback
        print(traceback.format_exc())
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
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 검색 결과 가져오기
    search_results = google_search(prompt)
    print(f"검색 결과: {search_results}")  # 디버깅용
    
    # 시스템 메시지 구성
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    
    # 검색 결과가 있으면 추가 컨텍스트 제공
    if search_results:
        context_message = f"""다음은 사용자의 질문과 관련된 최신 정보입니다:

{search_results}

위 정보를 참고하여 최신 정보를 포함해 답변해주세요."""
        
        messages.append({
            "role": "system",
            "content": context_message
        })
    
    # 대화 히스토리 추가
    messages.extend(st.session_state.messages)
    
    # AI 응답 생성 및 처리
    model_name = "gpt-4" if "GPT-4" in model else "gpt-3.5-turbo"
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
