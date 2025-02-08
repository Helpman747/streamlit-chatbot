import streamlit as st
from openai import OpenAI
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import json  # 디버깅용 추가
import re

# app.py 맨 위에 추가
print("Available secrets:", st.secrets)

# 페이지 설정
st.set_page_config(
    page_title="25th 3rd Soonicon ChatGPT",
    page_icon="🤖",
    layout="centered"  # wide에서 centered로 변경
)

# CSS 스타일 수정
st.markdown("""
<style>
/* 전체 페이지 배경 */
.stApp {
    background: #f7f7f8;
}

/* 헤더 배너 스타일 */
.banner-image {
    width: 850px;
    margin: 0 auto;
    display: block;
}

/* 전체 컨테이너 */
.main .block-container {
    max-width: 850px !important;
    margin: 0 auto !important;
    padding: 0 !important;
    background: white;
    min-height: 100vh;
    border-radius: 0;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

/* 메시지 영역 */
.messages-container {
    padding: 2rem;
    margin-bottom: 100px;  /* 입력창 높이만큼 여백 */
}

/* 메시지 스타일 */
.chat-message {
    padding: 1.5rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    white-space: pre-wrap;
}

.user-message {
    background-color: #f0f2f6;
}

.assistant-message {
    background-color: white;
    border: 1px solid #e0e0e0;
}

/* 입력창 영역 */
.input-area {
    position: fixed;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 850px;
    background: white;
    border-top: 1px solid #e5e5e5;
    padding: 1.5rem;
}

/* 소스 정보 스타일 */
.source-info {
    font-size: 0.8em;
    color: #666;
    border-top: 1px solid #eee;
    margin-top: 1rem;
    padding-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# 헤더 배너 추가
st.markdown(f'<img src="https://baegna.com/img/3rd.png" class="banner-image">', unsafe_allow_html=True)

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=st.secrets["openai_api_key"])

# 제목 제거 (이미 컨테이너 안에 포함될 것이므로)
# st.markdown('<h1 class="main-title">25th 3rd 수니콘미션 챗GPT</h1>', unsafe_allow_html=True)

# 시스템 프롬프트 수정
SYSTEM_PROMPT = """당신은 지식이 풍부한 AI 어시스턴트입니다.
주어진 검색 결과를 기반으로 정확하고 최신의 정보를 제공해야 합니다.

1. 검색 결과가 있는 경우:
   - 반드시 검색 결과의 내용을 기반으로 답변할 것
   - 검색 결과의 출처를 인용하며 설명할 것
   - 검색 결과에 없는 내용은 추측하지 말 것

2. 답변 형식:
   - 중요한 내용은 **강조**하여 표시
   - 필요한 경우 이모지 활용
   - 전문가적 문서처럼 보이게 답변
   - 최신정보도 포함해서 답변

3. 검색 결과가 없는 경우:
   - "죄송합니다. 해당 주제에 대한 검색 결과를 찾을 수 없습니다."라고 명시
   - 일반적인 정보만 제공

4. 답변 구조:
   - 개요
   - 주요 내용
   - 출처 정보
"""

# Google API 연결 테스트
def test_google_api():
    try:
        service = build("customsearch", "v1", developerKey=st.secrets["google_api_key"])
        test_result = service.cse().list(
            q="test",
            cx=st.secrets["google_cse_id"],
            num=1
        ).execute()
        return True
    except Exception as e:
        print(f"Google API 연결 실패: {str(e)}")
        return False

# 시작할 때 API 테스트 실행
print(test_google_api())

# Google 검색 함수 수정
def google_search(query, num_results=5):
    try:
        print(f"검색 시작: {query}")  # 디버깅
        
        # 검색 쿼리 전처리
        search_query = query.replace('"', '').replace('?', '').replace('!', '')
        
        # 한글 키워드 추출
        keywords = re.findall(r'[가-힣]+', search_query)
        
        # 불용어 제거
        stop_words = ["은", "는", "이", "가", "을", "를", "에", "의", "으로", "로", "도", "만", "것"]
        keywords = [word for word in keywords if word not in stop_words]
        
        # 최종 검색어 구성
        if "누구" in search_query or "어떤" in search_query:
            search_query = " ".join(keywords[:2])  # 주요 키워드 2개만 사용
        
        print(f"최종 검색 쿼리: {search_query}")  # 디버깅
        
        service = build("customsearch", "v1", developerKey=st.secrets["google_api_key"])
        
        try:
            result = service.cse().list(
                q=search_query,
                cx=st.secrets["google_cse_id"],
                num=num_results,
                lr='lang_ko',
                gl='kr',
                safe='off'  # 안전 검색 해제
            ).execute()
            
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
                print("검색 결과 없음 - items 키가 없음")  # 디버깅
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
    # 로고 이미지 추가
    st.image("logo.gif", width=200)  # 너비는 조절 가능
    
    st.markdown("### ⚙️ 모델 설정")
    model = st.selectbox(
        "모델 선택",
        ["GPT-4 (고성능)", "GPT-3.5 (빠른응답)"],
        format_func=lambda x: x.split(" ")[0]
    )
    
    st.markdown("---")
    
    # 사이트 설명 추가
    st.markdown("### ℹ️ 안내사항")
    st.markdown("""
    - 🔒 이 페이지는 **수니그룹 멤버 전용**으로 사용할수 있습니다.
    
    - 🎯 수니콘 미션을 대비한 **연습용 페이지** 입니다.
    
    - 💰 유료모델로 운영되기 때문에 과도하게 검색하시면, 제가 비용을 지불하게 됩니다.
    
    - 🔄 답변 스타일과 결과값은 더 잘나올수 있게 계속 업데이트 중입니다.
    
    - 👨‍💻 제작자: **HelpMan**
    """)
    
    st.markdown("---")
    st.markdown("### 💬 대화 기록")
    
    # 대화 기록이 있는 경우 표시
    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        for idx, msg in enumerate(st.session_state.messages[-10:]):
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
            "content": "이 챗봇은 수니콘 미션을 위해 제작된 챗봇입니다. 무엇이든 물어보세요! 😊"
        }
    ]

# 메시지 개수 제한 추가
MAX_MESSAGES = 20
if len(st.session_state.messages) > MAX_MESSAGES:
    # 최근 20개 메시지만 유지
    st.session_state.messages = st.session_state.messages[-MAX_MESSAGES:]

# 채팅 컨테이너 시작
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# 제목 부분 제거 (상단 배너로 대체)
# st.markdown('<h1 style="text-align: center; padding: 1rem;">25th 3rd 수니콘미션 챗GPT</h1>', unsafe_allow_html=True)

# 메시지 영역 시작
st.markdown('<div class="messages-container">', unsafe_allow_html=True)

# 메시지 표시 함수 추가
def format_message(content, role):
    if "제목:" in content and "내용:" in content and "출처:" in content:
        # 검색 결과를 포함한 메시지 포맷팅
        parts = content.split("\n\n")
        search_results = []
        sources = []
        
        for part in parts:
            if part.startswith("제목:"):
                lines = part.split("\n")
                title = lines[0].replace("제목: ", "")
                snippet = lines[1].replace("내용: ", "")
                source = lines[2].replace("출처: ", "")
                
                search_results.append(f"**{title}**\n{snippet}")
                sources.append(f"- [{title}]({source})")
        
        formatted_content = "\n\n".join(search_results)
        sources_section = "\n".join(sources)
        
        return f"""<div class="{role}-message chat-message">
{formatted_content}
<div class="source-info">출처:\n{sources_section}</div>
</div>"""
    else:
        return f'<div class="{role}-message chat-message">{content}</div>'

# 메시지 표시 부분 수정
for message in st.session_state.messages:
    st.markdown(
        format_message(message["content"], message["role"]),
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
                format_message(response, "assistant"),
                unsafe_allow_html=True
            )

    # 응답 저장
    st.session_state.messages.append({"role": "assistant", "content": response})

st.markdown('</div>', unsafe_allow_html=True)

# 채팅 컨테이너 종료
st.markdown('</div>', unsafe_allow_html=True)
