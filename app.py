import streamlit as st
from openai import OpenAI
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import json  # 디버깅용 추가
import re
import base64

# app.py 맨 위에 추가
print("Available secrets:", st.secrets)

# 페이지 설정
def get_base64_encoded_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

st.set_page_config(
    page_title="25th 3rd Soonicon ChatGPT",
    page_icon="logo.png",  # 🤖 대신 logo.png 사용
    layout="centered"
)

# CSS 파일 로드
with open("static/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 헤더 배너 추가
st.markdown(f'<img src="https://baegna.com/img/3rd.png" class="banner-image">', unsafe_allow_html=True)

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=st.secrets["openai_api_key"])

# 제목 제거 (이미 컨테이너 안에 포함될 것이므로)
# st.markdown('<h1 class="main-title">25th 3rd 수니콘미션 챗GPT</h1>', unsafe_allow_html=True)

# 시스템 프롬프트 수정
SYSTEM_PROMPT = """당신은 OpenAI의 ChatGPT입니다. 질문에 대해 체계적이고 전문적으로 답변해 주세요.

답변 형식:
1. 개요
   - 질문에 대한 명확한 정의나 설명
   - 주요 특징이나 중요 포인트

2. 주요 내용
   - 상세 설명과 분석
   - 관련된 중요 정보
   - 구체적인 예시나 사례

3. 구조화된 정보
   - 필요한 경우 목록화
   - 단계별 설명
   - 표나 분류 활용

4. 전달 방식
   - 객관적이고 전문적인 어조
   - **중요 내용** 강조
   - 단락 구분을 통한 가독성
   - 논리적 흐름 유지

5. 정보의 신뢰성
   - 정확한 정보 제공
   - 최신 데이터 활용
   - 객관적 시각 유지
   - 불확실한 정보는 명시
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

# 대화 컨텍스트 관리 함수 추가
def get_conversation_context(messages, current_query):
    # 최근 5개의 대화만 컨텍스트로 사용
    recent_messages = messages[-5:]
    context = []
    
    for msg in recent_messages:
        if msg["role"] == "user":
            context.append(f"사용자: {msg['content']}")
        elif msg["role"] == "assistant":
            context.append(f"AI: {msg['content']}")
    
    return "\n".join(context)

# format_message 함수 수정
def format_message(content, role):
    try:
        # 일반 메시지인 경우 바로 반환
        if "**" not in content or "[출처]" not in content:
            return f'<div class="{role}-message chat-message">{content}</div>'
        
        # 검색 결과를 포함한 메시지 포맷팅
        parts = content.split("\n\n")
        formatted_content = []
        
        for part in parts:
            try:
                if part.startswith("**"):
                    lines = part.split("\n")
                    # 최소한의 정보만 있어도 처리 가능하도록 수정
                    title = lines[0].replace("**", "") if lines else ""
                    snippet = lines[1] if len(lines) > 1 else ""
                    formatted_content.append(f"### {title}\n{snippet}")
                else:
                    formatted_content.append(part)
            except Exception as e:
                print(f"부분 처리 오류: {str(e)}")
                formatted_content.append(part)
        
        return f"""<div class="{role}-message chat-message">
{"\n\n".join(formatted_content)}
</div>"""
    except Exception as e:
        print(f"메시지 포맷팅 오류: {str(e)}")
        # 오류 발생 시 원본 내용 그대로 반환
        return f'<div class="{role}-message chat-message">{content}</div>'

# 검색 함수 수정
def google_search(query, context=""):
    try:
        # 검색 쿼리 전처리 및 확장
        search_query = query.replace('"', '').replace('?', '').replace('!', '')
        
        # 여러 검색 결과를 가져오기 위한 설정
        service = build("customsearch", "v1", developerKey=st.secrets["google_api_key"])
        
        # 첫 번째 검색: 일반 검색
        result1 = service.cse().list(
            q=search_query,
            cx=st.secrets["google_cse_id"],
            num=5,
            lr='lang_ko',
            gl='kr'
        ).execute()
        
        # 두 번째 검색: 최신 정보 검색
        result2 = service.cse().list(
            q=f"{search_query} 최신",
            cx=st.secrets["google_cse_id"],
            num=3,
            lr='lang_ko',
            gl='kr',
            sort='date'
        ).execute()
        
        # 세 번째 검색: 상세 정보 검색
        result3 = service.cse().list(
            q=f"{search_query} 상세정보 특징",
            cx=st.secrets["google_cse_id"],
            num=2,
            lr='lang_ko',
            gl='kr'
        ).execute()
        
        search_results = []
        seen_titles = set()  # 중복 제거를 위한 집합
        
        # 모든 검색 결과 통합 및 중복 제거
        for result in [result1, result2, result3]:
            if "items" in result:
                for item in result["items"]:
                    title = item.get('title', '')
                    snippet = item.get('snippet', '')
                    
                    # 중복 검사
                    if title not in seen_titles:
                        seen_titles.add(title)
                        
                        # 불필요한 정보 제거
                        snippet = re.sub(r'\.\.\.', '', snippet)
                        snippet = re.sub(r'\s+', ' ', snippet).strip()
                        
                        if title and snippet:
                            search_results.append(f"**{title}**\n{snippet}")
        
        # 검색 결과를 하나의 문자열로 결합
        return "\n\n".join(search_results)
    except Exception as e:
        print(f"검색 오류: {str(e)}")
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
        st.rerun()

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
for message in st.session_state.messages:
    st.markdown(
        format_message(message["content"], message["role"]),
        unsafe_allow_html=True
    )

# 메시지 영역 종료
st.markdown('</div>', unsafe_allow_html=True)

# 입력 영역
st.markdown('<div class="input-area">', unsafe_allow_html=True)

def handle_future_date_query(query):
    # 미래 날짜 감지
    future_date_pattern = r"(20[2-9][0-9]년\s*[0-9]{1,2}월\s*[0-9]{1,2}일?|20[2-9][0-9]년\s*[0-9]{1,2}월\s*첫째주|20[2-9][0-9]년\s*[0-9]{1,2}월\s*둘째주|20[2-9][0-9]년\s*[0-9]{1,2}월\s*셋째주|20[2-9][0-9]년\s*[0-9]{1,2}월\s*넷째주)"
    if re.search(future_date_pattern, query):
        return "죄송합니다, 미래의 정보는 제공할 수 없습니다. 대신 최신 정보를 제공해드리겠습니다. 최신 정보를 원하시면 재질문 해주시면 감사하겠습니다."
    return None

# 메시지 처리 부분 수정
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 미래 날짜 처리
    future_date_response = handle_future_date_query(prompt)
    if future_date_response:
        st.session_state.messages.append({"role": "assistant", "content": future_date_response})
        st.experimental_rerun()  # st.rerun() 대신 st.experimental_rerun() 사용
    else:
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
