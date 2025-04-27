import streamlit as st
import os
import re
import docx
import fitz  # PyMuPDF
import tempfile
from datetime import datetime
from gpt_helper_work_version import get_resume_analysis, generate_cover_letter

# Initialize session state variables
for key in ["gpt_result", "optimized_resume_path", "optimized_cover_letter_path", "company_name"]:
    if key not in st.session_state:
        st.session_state[key] = None

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
company_name_input = st.text_input("Company Name (optional)")
api_key = st.text_input("Enter your OpenAI API Key:", type="password")

analyze_btn = st.button("Analyze Resume")

if analyze_btn and uploaded_resume and uploaded_jd and api_key:
    with st.spinner("Extracting and analyzing..."):
        resume_text = extract_text(uploaded_resume)
        jd_text = extract_text(uploaded_jd)

        gpt_result = get_resume_analysis(resume_text, jd_text, api_key, include_replacements=True)

        # Store results in session state
        st.session_state["gpt_result"] = gpt_result

        company_name = company_name_input.strip() or "UnknownCompany"
        st.session_state["company_name"] = company_name

        # Save optimized resume
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_resume:
            doc = docx.Document()
            doc.add_paragraph(gpt_result)
            doc.save(tmp_resume.name)
            st.session_state["optimized_resume_path"] = tmp_resume.name

        # Generate and save cover letter
        cover_letter_text = generate_cover_letter(resume_text, jd_text, api_key)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_cover:
            doc = docx.Document()
            doc.add_paragraph(cover_letter_text)
            doc.save(tmp_cover.name)
            st.session_state["optimized_cover_letter_path"] = tmp_cover.name

# === Display Results if available ===
if st.session_state["gpt_result"]:
    st.subheader("GPT ATS Analysis Output")
    st.text_area("Raw Output", value=st.session_state["gpt_result"], height=400)

    resume_filename = f"Luiz_Resume_{st.session_state['company_name']}_v2.docx"
    cover_letter_filename = f"Cover_Letter_{st.session_state['company_name']}.docx"

    if st.session_state["optimized_resume_path"]:
        st.download_button(
            "Download Optimized Resume",
            open(st.session_state["optimized_resume_path"], "rb"),
            file_name=resume_filename
        )

    if st.session_state["optimized_cover_letter_path"]:
        st.download_button(
            "Download Cover Letter",
            open(st.session_state["optimized_cover_letter_path"], "rb"),
            file_name=cover_letter_filename
        )
