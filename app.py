import streamlit as st
import requests
from PyPDF2 import PdfReader
import anthropic
import re

def summarize_with_anthropic(api_key, text, model="claude-3-sonnet-20240320"):
    client = anthropic.Anthropic(api_key=api_key)
    
    try:
        message = client.messages.create(
            model=model,
            max_tokens=3000,
            temperature=0.7,
            system="You are an AI assistant tasked with summarizing a research paper in Korean. You have expertise in pathology, medicine, and the application of AI in pathology. Your audience is also a pathologist.",
            messages=[
                {
                    "role": "user",
                    "content": f"""Follow these instructions to create a concise and informative summary:

1. Use Korean for the summary, but keep the paper title, medical terms, and proper nouns in their original English form.
2. Write in a concise style, using endings like '~함', '~임' for brevity.
3. Use markdown format for better readability. Do not write in paragraph form.
4. Structure your summary as follows:
   a. Title:
      - Format: ## [Original English Title] (출간년도)
   b. Keywords:
      - List approximately 5 key terms from the paper
   c. Overall Summary:
      - Provide a 3-line summary of the entire paper
   d. Detailed Section Summaries:
      - Summarize each of the following sections in about 5 lines each:
        - Introduction
        - Method
        - Result
        - Discussion
5. Do not summarize anything after the 'References' section.
6. Ensure all medical terms, proper nouns, and other specialized vocabulary remain in English.

Present your summary within <summary> tags. Remember to use markdown formatting for headers and list items.

Text to summarize:

{text}"""
                }
            ]
        )
        return message.content
    except anthropic.APIError as e:
        st.error(f"API 오류: {str(e)}")
        return "Error: Failed to summarize the text."

# Streamlit 앱 시작
st.title("논문 요약 웹앱")

# API Key 입력 섹션
api_key = st.text_input("Anthropic API Key를 입력하세요", type="password")

# API 키 검증
if api_key:
    client = anthropic.Anthropic(api_key=api_key)
    try:
        # API 키 유효성을 간단히 확인하는 요청
        response = client.completions.create(
            model="claude-2.1",
            max_tokens_to_sample=10,
            prompt="Hello, World!",
        )
        if response:
            st.success("API 키가 유효합니다.")
        else:
            st.error("API 응답을 받지 못했습니다. API 키를 다시 확인해주세요.")
    except Exception as e:
        st.error(f"API 키 검증 중 오류가 발생했습니다: {str(e)}")
        api_key = None

# 파일 업로드 섹션
uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])

# URL 입력 섹션
url = st.text_input("논문 URL을 입력하세요")

# 요약하기 버튼 추가
if st.button("요약하기"):
    if api_key:
        if uploaded_file is not None:
            # PDF 파일에서 텍스트 추출
            pdf_reader = PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            # Anthropic API를 사용하여 요약을 수행합니다.
            summary = summarize_with_anthropic(api_key, text)
            
            # 요약 결과 처리 및 출력
            summary_content = summary
            if summary.startswith("TextBlock(text='"):
                # TextBlock 형식에서 실제 내용만 추출
                summary_content = re.search(r"text='(.*?)'", summary, re.DOTALL).group(1)
            # 이스케이프된 줄바꿈 문자를 실제 줄바꿈으로 변환
            summary_content = summary_content.replace('\\n', '\n')
            # <summary> 태그 제거
            summary_content = re.sub(r'</?summary>', '', summary_content).strip()
            
            st.markdown(summary_content)

        elif url:
            response = requests.get(url)
            if response.status_code == 200:
                text = response.text
                
                # Anthropic API를 사용하여 요약을 수행합니다.
                summary = summarize_with_anthropic(api_key, text)
                
                # 요약 결과 처리 및 출력 (PDF와 동일한 처리)
                summary_content = summary
                if summary.startswith("TextBlock(text='"):
                    summary_content = re.search(r"text='(.*?)'", summary, re.DOTALL).group(1)
                summary_content = summary_content.replace('\\n', '\n')
                summary_content = re.sub(r'</?summary>', '', summary_content).strip()
                
                st.markdown(summary_content)
            else:
                st.write("URL을 가져올 수 없습니다. 다시 시도해주세요.")
        else:
            st.write("파일을 업로드하거나 URL을 입력해주세요.")
    else:
        st.write("API Key를 입력해주세요.")
