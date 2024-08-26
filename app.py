import anthropic
import streamlit as st
import requests
from PyPDF2 import PdfReader
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
import re
from docx import Document
import io
import pyperclip

def summarize_with_anthropic(api_key, text, model="claude-3-5-sonnet-20240620"):
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""Follow these instructions to create a concise and informative summary:

1. Use Korean for the summary, but keep the paper title, medical terms, and proper nouns in their original English form.
    Examples of medical terms: "colon adenocarcinoma", "eosinophils", "neuroblastoma", "leiomyoma", "mesangium", "intrinsic cells"
2. Write in a concise style, using endings like '~함', '~임' for brevity.
3. Use markdown format for better readability. Do not write in paragraph form.
4. Structure your summary as follows:
   a. Title:
      - Format: ## [Original English Title] (published year)
   b. Keywords:
      - List approximately 5 key terms from the paper. 한눈에 알아보기 쉽게 각 단어가 시각적으로 잘 구분될 수 있게 출력하기
          (examples: "colon adenocarcinoma", "object detection", "neuropathology")
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

    try:
        with st.empty():
            stream = client.messages.create(
                model=model,
                max_tokens=3000,
                temperature=0.3,
                system="You are an AI assistant tasked with summarizing a research paper in Korean. You have expertise in pathology, medicine, and the application of AI in pathology. Your audience is also a pathologist.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                stream=True
            )
            response = ""
            for chunk in stream:
                if chunk.type == "content_block":
                    response += chunk.text
                    st.markdown(response)
        return response
    except Exception as e:
        st.error(f"API 오류: {str(e)}")
        return "Error: Failed to summarize the text."

# 페이지 설정
st.set_page_config(
    page_title="📝병리논문요약",
    page_icon="📝",
)

# UI 제목
st.title("병리 논문 요약하기📝_ver2 (HJY)")


# API Key 입력 섹션
api_key = st.text_input("Anthropic API Key를 입력하세요", type="password")

# API 키 검증
if api_key:
    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=10,
            messages=[
                {"role": "user", "content": "Hello, World!"}
            ]
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


# 요약하기 버튼을 누를 때 실행되는 부분
if st.button("요약하기"):
    if api_key:
        if uploaded_file is not None:
            # PDF 파일에서 텍스트 추출
            pdf_reader = PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
           # 요약 중 메시지 표시
            with st.spinner("논문 요약 중입니다..."):
                try:
                    # Anthropic API를 사용하여 요약을 수행합니다.
                    summary = summarize_with_anthropic(api_key, text)
                    
                    # 요약 결과 처리 및 출력
                    summary_content = summary
                    # <summary> 태그 제거
                    summary_content = re.sub(r'</?summary>', '', summary_content).strip()
                    
                    st.markdown(summary_content)
                except Exception as e:
                    st.error(f"요약 중 오류 발생: {str(e)}")
            
            st.markdown(summary_content)
            
            if summary_content:
                if st.button("결과 복사"):
                    pyperclip.copy(summary_content)
                    st.success("결과가 클립보드에 복사되었습니다.")

                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("TXT 파일로 저장"):
                        txt_io = io.StringIO()
                        txt_io.write(summary_content)
                        st.download_button(
                            label="Download TXT",
                            data=txt_io.getvalue(),
                            file_name="summary.txt",
                            mime="text/plain"
                        )
                
                with col2:
                    if st.button("DOCX 파일로 저장"):
                        doc = Document()
                        doc.add_paragraph(summary_content)
                        docx_io = io.BytesIO()
                        doc.save(docx_io)
                        docx_io.seek(0)
                        st.download_button(
                            label="Download DOCX",
                            data=docx_io,
                            file_name="summary.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )

        elif url:
            try:
                # User-Agent 헤더 추가 및 세션 사용
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                session = requests.Session()
                response = session.get(url, headers=headers, timeout=10)
                response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

                st.write(f"Status Code: {response.status_code}")
                st.write(f"Content Type: {response.headers.get('Content-Type')}")

                if response.status_code == 200:
                    if 'application/pdf' in response.headers.get('Content-Type', ''):
                        # PDF 파일 처리
                        pdf_file = io.BytesIO(response.content)
                        pdf_reader = PdfReader(pdf_file)
                        text = ""
                        for page in pdf_reader.pages:
                            text += page.extract_text()
                    else:
                        # 일반 텍스트 처리
                        text = response.text

                    # 텍스트 길이 제한 (예: 최대 100,000자)
                    max_length = 100000
                    if len(text) > max_length:
                        text = text[:max_length]
                        st.warning(f"텍스트가 너무 길어 처음 {max_length}자만 사용합니다.")

                    # 텍스트 내용 일부 출력 (디버깅용)
                    st.write("Text Preview:")
                    st.write(text[:500] + "...")  # 처음 500자만 출력

                    # Anthropic API를 사용하여 요약을 수행합니다.
                    summary = summarize_with_anthropic(api_key, text)

                    # 요약 결과 처리 및 출력
                    summary_content = summary
                    # <summary> 태그 제거
                    summary_content = re.sub(r'</?summary>', '', summary_content).strip()

                    st.markdown(summary_content)
                else:
                    st.error(f"URL에서 데이터를 가져오는 데 실패했습니다. 상태 코드: {response.status_code}")
            
            except requests.exceptions.RequestException as e:
                    st.error(f"URL 요청 중 오류 발생: {str(e)}")
            except Exception as e:
                    st.error(f"예상치 못한 오류 발생: {str(e)}")
        else:
            st.warning("PDF 파일을 업로드하거나 URL을 입력해주세요.")
    else:
        st.error("유효한 API 키를 입력해주세요.")
