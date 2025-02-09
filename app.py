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
SYSTEM_PROMPT = """당신은 지식이 풍부한 AI 어시스턴트입니다. 이전 대화 내용을 기억하고 맥락을 이해하여 답변해야 합니다.

1. 미래 날짜 처리:
   - 미래 날짜가 포함된 질문을 인식
   - 미래 정보를 제공할 수 없음을 명확히 설명
   - 가장 최신 정보나 관련된 유사 정보를 제안

2. 답변 구조:
   📌 개요
   - 질문에 대한 핵심 답변을 1-2문장으로 요약
   - 이전 대화와 연결되는 부분 언급

   📑 상세 내용
   - 주요 내용을 섹션별로 구분하여 설명
   - 각 섹션은 소제목과 함께 제시
   - 중요한 내용은 **강조** 표시
   - 목록이나 단계가 필요한 경우 번호 매기기 사용

   💡 추가 정보
   - 관련된 흥미로운 사실이나 통계
   - 실제 사례나 예시 포함

3. 형식 가이드:
   - 각 섹션 사이에 빈 줄 추가하여 가독성 확보
   - 긴 문단은 피하고 2-3문장으로 분리
   - 중요한 수치나 날짜는 굵게 표시
   - 적절한 이모지로 섹션 구분
   - 표나 목록 활용하여 정보 구조화

4. 맥락 관리:
   - 이전 대화 내용 참조 시 "이전 대화에서 언급된..."
   - 새로운 정보 추가 시 "추가 정보로는..."
   - 관련 후속 질문 2-3개 제안

5. 검색 결과 활용:
   - 검색 결과와 이전 대화 내용을 자연스럽게 통합
   - 최신 정보 우선 활용

6. 전문성 유지:
   - 공식적이고 전문적인 어조 사용
   - 정확한 용어와 설명 제공
   - 불확실한 정보는 "~로 알려져 있습니다" 형식 사용
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
        # 검색 쿼리 전처리
        search_query = query.replace('"', '').replace('?', '').replace('!', '')
        
        # 검색 실행
        service = build("customsearch", "v1", developerKey=st.secrets["google_api_key"])
        result = service.cse().list(
            q=search_query,
            cx=st.secrets["google_cse_id"],
            num=5,
            lr='lang_ko',
            gl='kr',
            safe='off'
        ).execute()
        
        if "items" in result:
            search_results = []
            
            for item in result["items"]:
                try:
                    title = item.get('title', '')
                    snippet = item.get('snippet', '')
                    
                    # 불필요한 정보 제거
                    snippet = re.sub(r'\.\.\.', '', snippet)  # ... 제거
                    snippet = re.sub(r'\s+', ' ', snippet).strip()  # 공백 정리
                    
                    # 검색 결과 추가 (출처 정보 제외)
                    if title and snippet:
                        search_results.append(f"**{title}**\n{snippet}")
                except Exception as e:
                    print(f"검색 결과 처리 오류: {str(e)}")
                    continue
            
            return "\n\n".join(search_results)
        return ""
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
