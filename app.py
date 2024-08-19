import streamlit as st
import requests

# Anthropic API를 호출하여 요약을 수행하는 함수
def summarize_with_anthropic(api_key, text, model="claude-3-5-sonnet-20240620"):
    url = "https://api.anthropic.com/v1/complete"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    prompt = (
        "You are an AI assistant tasked with summarizing a research paper in Korean. "
        "You have expertise in pathology, medicine, and the application of AI in pathology. "
        "Your audience is also a pathologist. Follow these instructions to create a concise and informative summary:\n\n"
        "1. Use Korean for the summary, but keep the paper title, medical terms, and proper nouns in their original English form.\n"
        "2. Write in a concise style, using endings like '~함', '~임' for brevity.\n"
        "3. Use markdown format for better readability. Do not write in paragraph form.\n"
        "4. Structure your summary as follows:\n"
        "   a. Title:\n"
        "      - Format: ## [Original English Title] (출간년도)\n"
        "   b. Keywords:\n"
        "      - List approximately 5 key terms from the paper\n"
        "   c. Overall Summary:\n"
        "      - Provide a 3-line summary of the entire paper\n"
        "   d. Detailed Section Summaries:\n"
        "      - Summarize each of the following sections in about 5 lines each:\n"
        "        - Introduction\n"
        "        - Method\n"
        "        - Result\n"
        "        - Discussion\n"
        "5. Do not summarize anything after the 'References' section.\n"
        "6. Ensure all medical terms, proper nouns, and other specialized vocabulary remain in English.\n\n"
        "Present your summary within <summary> tags. Remember to use markdown formatting for headers and list items.\n\n"
        "Text to summarize:\n\n" + text
    )
    
    payload = {
        "model": model,
        "prompt": prompt,
        "max_tokens_to_sample": 3000,  # 적절한 최대 토큰 수 설정
        "temperature": 0.7
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        return result.get("completion", "").strip()
    else:
        return "Error: Failed to summarize the text."

st.title("논문 요약 웹앱")

# API Key 입력 섹션
api_key = st.text_input("Anthropic API Key를 입력하세요", type="password")

# 파일 업로드 섹션
uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])
if uploaded_file is not None and api_key:
    from PyPDF2 import PdfReader

    # PDF 파일을 읽습니다.
    pdf_reader = PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    
    # Anthropic API를 사용하여 요약을 수행합니다.
    summary = summarize_with_anthropic(api_key, text)
    st.write("요약 결과:")
    st.write(summary)

# URL 입력 섹션
url = st.text_input("논문 URL을 입력하세요")
if url and api_key:
    response = requests.get(url)
    if response.status_code == 200:
        text = response.text
        
        # Anthropic API를 사용하여 요약을 수행합니다.
        summary = summarize_with_anthropic(api_key, text)
        st.write("요약 결과:")
        st.write(summary)
    else:
        st.write("URL을 가져올 수 없습니다. 다시 시도해주세요.")