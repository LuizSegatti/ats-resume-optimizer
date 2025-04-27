import streamlit as st
import os
import re
import docx
import fitz  # PyMuPDF
import tempfile
from datetime import datetime
from gpt_helper_work_version import get_resume_analysis, generate_cover_letter

# === Helper Functions ===
def extract_text(file):
    ext = file.name.lower()
    if ext.endswith(".pdf"):
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = "\n".join([page.get_text() for page in doc])
        doc.close()
        return text
    elif ext.endswith(".docx"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name
        doc = docx.Document(tmp_path)
        return "\n".join([p.text for p in doc.paragraphs])
    return ""

# === Streamlit UI ===
st.set_page_config(page_title="ATS Resume Optimizer", layout="wide")
st.title("📄 ATS Resume Optimizer – GPT Enhanced")

uploaded_resume = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx"], key="resume")
uploaded_jd = st.file_uploader("Upload Job Description (PDF/DOCX)", type=["pdf", "docx"], key="jd")
company_name_input = st.text_input("Company Name (leave blank to auto-detect)")
api_key = st.text_input("Enter your OpenAI API Key:", type="password")

analyze_btn = st.button("Analyze Resume")

if analyze_btn and uploaded_resume and uploaded_jd:
    with st.spinner("Extracting and analyzing..."):
        resume_text = extract_text(uploaded_resume)
        jd_text = extract_text(uploaded_jd)

        gpt_result = get_resume_analysis(resume_text, jd_text, api_key, include_replacements=True)
        
        st.subheader("GPT ATS Analysis Output")
        st.text_area("Raw Output", value=gpt_result, height=400)

        # Detect company name
        company_name = company_name_input.strip() or "UnknownCompany"

        # Extract replacements
        replacements = []

        # Apply replacements to resume
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(uploaded_resume.getbuffer())
            resume_file_path = tmp.name

        doc = docx.Document(resume_file_path)
        resume_filename = f"Luiz_Resume_{company_name}_v2.docx"
        out_path = os.path.join(tempfile.gettempdir(), resume_filename)

        doc.save(out_path)

        # Extract score
        score = "N/A"

        # Display Results
        st.success(f"✅ Compatibility Score: {score}% for {company_name}")
        st.download_button("Download Optimized Resume", open(out_path, "rb"), file_name=resume_filename)

        # Generate Cover Letter
        cover_letter_text = generate_cover_letter(resume_text, jd_text, api_key)

        cover_filename = f"Cover_Letter_{company_name}.docx"
        cover_path = os.path.join(tempfile.gettempdir(), cover_filename)

        doc = docx.Document()
        doc.add_paragraph(cover_letter_text)
        doc.save(cover_path)

        st.download_button("Download Cover Letter", open(cover_path, "rb"), file_name=cover_filename)
