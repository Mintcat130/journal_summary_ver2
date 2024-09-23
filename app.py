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
        - Conclusion
5. Do not summarize anything after the 'References' section.
6. Ensure all medical terms, proper nouns, and other specialized vocabulary remain in English.

Remember to use markdown formatting for headers and list items.
요약 내용 말고 다른 말은 아무것도 적지 말것

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
    except Exception as e:
        raise Exception(f"API 오류: {str(e)}")

# 페이지 설정
st.set_page_config(
    page_title="📝병리논문요약",
    page_icon="📝",
)

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
url = st.text_input("논문 URL을 입력하세요. PDF 파일이 나타나는 페이지의 링크여야 합니다. 예시)https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7433998/pdf/tjg-31-6-441.pdf ")



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
                    st.success("요약이 완료되었습니다.")  # 성공 메시지만 표시
                except Exception as e:
                    st.error(f"요약 중 오류 발생: {str(e)}")
        else:
            st.warning("PDF 파일을 업로드하거나 유효한 URL을 입력해주세요.")
    else:
        st.error("유효한 API 키를 입력해주세요.")

# 요약 결과 표시 및 버튼 생성
if 'summary_content' in st.session_state and 'original_text' in st.session_state:
    st.markdown(st.session_state.summary_content)

    col1, col2 = st.columns(2)
    
    with col1:
        if st.download_button(
            label="TXT 파일로 저장",
            data=st.session_state.summary_content,
            file_name="summary.txt",
            mime="text/plain",
            key="txt_download"
        ):
            st.success("TXT 파일이 다운로드되었습니다.")

    with col2:
        docx_io = io.BytesIO()
        doc = Document()
        doc.add_paragraph(st.session_state.summary_content)
        doc.save(docx_io)
        docx_io.seek(0)
        
        if st.download_button(
            label="DOCX 파일로 저장",
            data=docx_io,
            file_name="summary.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="docx_download"
        ):
            st.success("DOCX 파일이 다운로드되었습니다.")

# 새로운 버튼 추가
if st.button("한번 더 다르게 요약해보기"):
    with st.spinner("다시 요약 중입니다..."):
        try:
            new_summary = summarize_with_anthropic(api_key, st.session_state.original_text)
            new_summary_content = re.sub(r'</?summary>', '', new_summary).strip()
            new_summary_content = re.sub(r'^Here is a summary of the research paper in Korean:\s*', '', new_summary_content, flags=re.IGNORECASE)
            st.markdown("## 새로운 요약")
            st.markdown(new_summary_content)

            # 새로운 요약 결과에 대한 파일 저장 버튼
            col1, col2 = st.columns(2)
            with col1:
                if st.download_button(
                    label="새 요약 TXT로 저장",
                    data=new_summary_content,
                    file_name="new_summary.txt",
                    mime="text/plain",
                    key="new_txt_download"
                ):
                    st.success("새로운 요약 TXT 파일이 다운로드되었습니다.")

            with col2:
                docx_io = io.BytesIO()
                doc = Document()
                doc.add_paragraph(new_summary_content)
                doc.save(docx_io)
                docx_io.seek(0)
                
                if st.download_button(
                    label="새 요약 DOCX로 저장",
                    data=docx_io,
                    file_name="new_summary.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="new_docx_download"
                ):
                    st.success("새로운 요약 DOCX 파일이 다운로드되었습니다.")

        except Exception as e:
            st.error(f"새로운 요약 중 오류 발생: {str(e)}")

if st.button("더 길고 디테일하게 요약해보기"):
    with st.spinner("상세 요약 중입니다..."):
        try:
            detailed_prompt = f"""Follow these instructions to create a more detailed summary:

1. Use Korean for the summary, but keep the paper title, medical terms, and proper nouns in their original English form.
2. Write in a concise style, using endings like '~함', '~임' for brevity.
3. Use markdown format for better readability. Do not write in paragraph form.
4. Structure your summary as follows:
   a. Title:
      - Format: ## [Original English Title] (published year)
   b. Keywords:
      - List approximately 5 key terms from the paper.
   c. Overall Summary:
      - Provide a 5-line summary of the entire paper
   d. Detailed Section Summaries:
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

Text to summarize:

{st.session_state.original_text}"""

            detailed_system_prompt = "You are an AI assistant tasked with creating detailed summaries of research papers in Korean. Your summaries should be thorough and follow the given instructions precisely."
            
            detailed_summary = summarize_with_anthropic(api_key, detailed_prompt, system_prompt=detailed_system_prompt)
            detailed_summary_content = re.sub(r'</?summary>', '', detailed_summary).strip()
            detailed_summary_content = re.sub(r'^Here is a more detailed summary of the research paper in Korean:\s*', '', detailed_summary_content, flags=re.IGNORECASE)
            st.markdown("## 상세 요약")
            st.markdown(detailed_summary_content)

            # 상세 요약 결과에 대한 파일 저장 버튼
            col1, col2 = st.columns(2)
            with col1:
                if st.download_button(
                    label="상세 요약 TXT로 저장",
                    data=detailed_summary_content,
                    file_name="detailed_summary.txt",
                    mime="text/plain",
                    key="detailed_txt_download"
                ):
                    st.success("상세 요약 TXT 파일이 다운로드되었습니다.")

            with col2:
                docx_io = io.BytesIO()
                doc = Document()
                doc.add_paragraph(detailed_summary_content)
                doc.save(docx_io)
                docx_io.seek(0)
                
                if st.download_button(
                    label="상세 요약 DOCX로 저장",
                    data=docx_io,
                    file_name="detailed_summary.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="detailed_docx_download"
                ):
                    st.success("상세 요약 DOCX 파일이 다운로드되었습니다.")

        except Exception as e:
            st.error(f"상세 요약 중 오류 발생: {str(e)}")
            st.error("오류 상세 정보:")
            st.error(str(e))  # 더 자세한 오류 정보 표시
else:
    st.warning("먼저 논문을 요약해주세요.")

