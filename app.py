import anthropic
import streamlit as st
import requests
from PyPDF2 import PdfReader
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
import re
from docx import Document
import io


# 여기에 새 코드를 추가합니다
if 'original_text' not in st.session_state:
    st.session_state.original_text = ""

def summarize_with_anthropic(api_key, text, model="claude-3-5-sonnet-20240620", system_prompt="You are an AI assistant tasked with summarizing a research paper in Korean. You have expertise in pathology, medicine, and the application of AI in pathology. Your audience is also a pathologist."):
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Follow these instructions to create a concise and informative summary:

1. Use Korean for the summary, but keep the paper title, author names, medical terms, and proper nouns in their original English form.
2. Write in a concise style, using endings like '~함', '~임' for brevity.
3. Use markdown format for better readability. Do not write in paragraph form.
4. Structure your summary as follows:
   a. Title:
      - Format: ## [Original English Title] (published year)
   b. Authors:
      - List the authors' names in the original English form
      - Format: ** Authors: [Author1], [Author2], ... **
   c. Keywords:
      - List approximately 5 key terms from the paper. 
      - Format each keyword with backticks, like this: `keyword`
      - Example: "Keywords: `colon adenocarcinoma`, `object detection`, `neuropathology`"
   d. Overall Summary:
      - Provide a 3-line summary of the entire paper
   e. Detailed Section Summaries:
      - Summarize each of the following sections in about 5 lines each:
        - Introduction
        - Method
        - Result
        - Discussion
        - Conclusion
5. Do not summarize anything after the 'References' section.
6. Ensure all medical terms, proper nouns, and other specialized vocabulary remain in English.
7. 요약 내용 이외 불필요한 말은 아무것도 하지 말것.

Remember to use markdown formatting for headers and list items.

Text to summarize:

{text}"""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            temperature=0.3,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return response.content[0].text
    except anthropic.APIError as e:
        if e.status_code == 529:
            raise Exception("API가 현재 과부하 상태입니다. 잠시 후 다시 시도해 주세요.")
        else:
            raise Exception(f"API 오류: {str(e)}")

# 페이지 설정
st.set_page_config(
    page_title="📝병리논문요약",
    page_icon="📝",
)

# CSS를 사용하여 코드 블록의 높이를 제한합니다.
st.markdown("""
<style>
    .stCode {
        max-height: 200px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# UI 제목
st.title("병리 논문 요약하기📝_ver2 (HJY)")


# API Key 입력 섹션
api_key = st.text_input("Anthropic API Key를 입력 후 엔터를 누르세요", type="password")

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


# 파일 업로드 및 URL 입력 섹션
uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])
url = st.text_input("논문 URL을 입력하세요. PDF 파일이 나타나는 페이지의 링크여야 합니다. [예시 링크](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7433998/pdf/tjg-31-6-441.pdf) ")



# 요약하기 버튼을 누를 때 실행되는 부분
if st.button("요약하기"):
    if api_key:
        text = ""
        if uploaded_file is not None:
            # PDF 파일에서 텍스트 추출
            pdf_reader = PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        elif url:
            try:
                # User-Agent 헤더 추가 및 세션 사용
                headers = {
                     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                session = requests.Session()
                response = session.get(url, headers=headers, timeout=10)
                response.raise_for_status()
        
                if response.status_code == 200:
                    if 'application/pdf' in response.headers.get('Content-Type', ''):
                        pdf_file = io.BytesIO(response.content)
                        pdf_reader = PdfReader(pdf_file)
                        for page in pdf_reader.pages:
                            text += page.extract_text()
                    else:
                        text = response.text
        
                    max_length = 100000
                    if len(text) > max_length:
                        text = text[:max_length]
                        st.warning(f"텍스트가 너무 길어 처음 {max_length}자만 사용합니다.")
                else:
                    st.error(f"URL에서 데이터를 가져오는 데 실패했습니다. 상태 코드: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error("URL에서 PDF를 직접 다운로드할 수 없습니다. 다음 방법을 시도해보세요:")
                st.markdown("""
                1. PDF 파일을 다운로드 후 직접 업로드해주세요.
                2. 공개적으로 접근 가능한 URL을 사용해주세요.
                """)
                text = ""
            except Exception as e:
                st.error(f"예상치 못한 오류 발생: {str(e)}")
                text = ""
        
        if text:
            # 원본 텍스트를 세션 상태에 저장
            st.session_state.original_text = text
            
            with st.spinner("논문 요약 중입니다..."):
                try:
                    summary = summarize_with_anthropic(api_key, st.session_state.original_text)
                    summary_content = re.sub(r'</?summary>', '', summary).strip()
                    summary_content = re.sub(r'^Here is a summary of the research paper in Korean:\s*', '', summary_content, flags=re.IGNORECASE)
                    st.session_state.summary_content = summary_content
                    st.success("요약이 완료되었습니다.")
                except Exception as e:
                    st.error(f"요약 중 오류 발생: {str(e)}")
                    if "과부하 상태" in str(e):
                        st.info("API 서버가 현재 많은 요청을 처리하고 있습니다. 잠시 후에 다시 시도해 주세요.")
                    else:
                        st.info("예기치 못한 오류가 발생했습니다. 문제가 지속되면 관리자에게 문의해 주세요.")
        else:
            st.warning("PDF 파일을 업로드하거나 유효한 URL을 입력해주세요.")
    else:
        st.error("유효한 API 키를 입력해주세요.")

# 요약 결과 표시 및 버튼 생성
if 'summary_content' in st.session_state and 'original_text' in st.session_state:
    st.markdown(st.session_state.summary_content)
    
    st.markdown("### 요약 내용 복사")
    st.text("코드블럭에 커서를 올리면 우측 상단에 생성되는 복사 버튼을 눌러 내용을 클립보드에 복사 가능합니다")
    st.code(st.session_state.summary_content, language="markdown")

if st.button("더 길고 디테일하게 요약해보기"):
    if api_key:  # API 키가 입력되었는지 확인
        with st.spinner("상세 요약 중입니다..."):
            try:
                detailed_prompt = f"""Follow these instructions to create a more detailed summary:
                1. Use Korean for the summary, but keep the paper title, medical terms, and proper nouns in their original English form.
                2. Write in a concise style, using endings like '~함', '~임' for brevity.
                3. Use markdown format for better readability. Do not write in paragraph form.
                4. Structure your summary as follows:
                   a. Title:
                      - Format: ## [Original English Title] (published year)
                   b. Authors:
                      - List the authors' names in the original English form
                      - Format: **Authors: [Author1], [Author2], ... **
                   c. Keywords:
                      - List approximately 5 key terms from the paper.
                      - Format each keyword with backticks, like this: `keyword`
                   d. Overall Summary:
                      - Provide a 5-line summary of the entire paper
                   e. Detailed Section Summaries:
                      - IMPORTANT: Summarize each of the following sections in about 10 lines. 
                      - Use bullet points for each line per section.
                      - Sections to summarize:
                        • Introduction
                        • Method
                        • Result
                        • Discussion
                        • Conclusion
                5. Do not summarize anything after the 'References' section.
                6. Ensure all medical terms, proper nouns, and other specialized vocabulary remain in English.
                7. REMINDER: Each section summary MUST be more than 5 lines long. This is crucial for the desired output format.
                8. 요약 내용 이외 불필요한 말은 아무것도 하지 말것.

                Text to summarize:

                {st.session_state.original_text}"""

                detailed_system_prompt = "You are an AI assistant tasked with creating detailed summaries of research papers in Korean. Your summaries should be thorough and follow the given instructions precisely."
                
                detailed_summary = summarize_with_anthropic(api_key, detailed_prompt, system_prompt=detailed_system_prompt)
                detailed_summary_content = re.sub(r'</?summary>', '', detailed_summary).strip()
                detailed_summary_content = re.sub(r'^Here is a more detailed summary of the research paper in Korean:\s*', '', detailed_summary_content, flags=re.IGNORECASE)
                st.markdown("## 상세 요약")
                st.markdown(detailed_summary_content)
                
                st.markdown("### 상세 요약 내용 복사")
                st.text("코드블럭에 커서를 올리면 우측 상단에 생성되는 복사 버튼을 눌러 내용을 클립보드에 복사 가능합니다")
                st.code(detailed_summary_content, language="markdown")

            except Exception as e:
                st.error(f"상세 요약 중 오류 발생: {str(e)}")
                st.error("오류 상세 정보:")
                st.error(str(e))
    else:
        st.error("유효한 API 키를 입력해주세요.")
else:
    st.warning("먼저 논문을 요약해주세요.")
