import streamlit as st
import os
import re
import docx
import fitz  # PyMuPDF
import tempfile
import json
from datetime import datetime
from docx.shared import Pt
from gpt_helper_work_version import get_resume_analysis, generate_cover_letter

# Initialize session state variables
for key in ["gpt_result", "optimized_resume_path", "optimized_cover_letter_path", "company_name", "candidate_name", "replacements"]:
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

# Function to parse replacements from GPT output
def parse_replacements_from_output(gpt_output):
    try:
        matches = re.findall(r'Replace \"(.*?)\" with \"(.*?)\"', gpt_output)
        return matches
    except Exception as e:
        return []

# Function to apply replacements to DOCX file
def apply_replacements_to_docx(original_path, replacements):
    doc = docx.Document(original_path)
    changes = []
    for para in doc.paragraphs:
        for old, new in replacements:
            if old.lower() in para.text.lower():
                pattern = re.compile(re.escape(old), re.IGNORECASE)
                updated_text = pattern.sub(new, para.text)
                if updated_text != para.text:
                    para.text = updated_text
                    changes.append((old, new))
    return doc, changes

# Function to extract Company Name from JD
def extract_company_name_from_jd(jd_text):
    company_line = re.search(r'Company:\s*(.*)', jd_text, re.IGNORECASE)
    if company_line:
        return company_line.group(1).strip()
    patterns = [
        r'About\s+(.*?)\s+is\s+a',
        r'Join\s+(.*?)\s+as',
        r'work at\s+(.*?)\s',
        r'careers at\s+(.*?)\s',
    ]
    for pattern in patterns:
        match = re.search(pattern, jd_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "UnknownCompany"

# Function to extract Candidate Name from GPT output
def extract_candidate_name_from_gpt(gpt_output):
    candidate_line = re.search(r'Name:\s*(.*)', gpt_output, re.IGNORECASE)
    if candidate_line:
        return candidate_line.group(1).strip()
    return "UnknownCandidate"

# === Streamlit UI ===
st.set_page_config(page_title="ATS Resume Optimizer", layout="wide")
st.title("📄 ATS Resume Optimizer v1.0.3 – GPT Enhanced")

uploaded_resume = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx"], key="resume")
uploaded_jd = st.file_uploader("Upload Job Description (PDF/DOCX)", type=["pdf", "docx"], key="jd")
company_name_input = st.text_input("Company Name (optional)")
api_key = st.text_input("Enter your OpenAI API Key:", type="password")

analyze_btn = st.button("Analyze Resume")

if analyze_btn and uploaded_resume and uploaded_jd and api_key:
    ext = uploaded_resume.name.lower()
    if not ext.endswith(".docx"):
        st.error("Resume optimization currently supports DOCX files only. Please upload a .docx resume.")
    else:
        with st.spinner("Extracting and analyzing..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_resume:
                tmp_resume.write(uploaded_resume.getbuffer())
                resume_path = tmp_resume.name

            resume_text = extract_text(uploaded_resume)
            jd_text = extract_text(uploaded_jd)

            gpt_result = get_resume_analysis(resume_text, jd_text, api_key, include_replacements=True)
            st.session_state["gpt_result"] = gpt_result

            replacements = parse_replacements_from_output(gpt_result)
            st.session_state["replacements"] = replacements

            company_name = company_name_input.strip()
            if not company_name:
                company_name = extract_company_name_from_jd(jd_text)
            st.session_state["company_name"] = company_name

            candidate_name = extract_candidate_name_from_gpt(gpt_result)
            st.session_state["candidate_name"] = candidate_name

            # === Improved Resume Generation ===
            updated_doc, changes = apply_replacements_to_docx(resume_path, replacements)

            improved_resume_filename = f"Luiz_Resume_{company_name}_v2.docx"
            improved_resume_path = os.path.join(tempfile.gettempdir(), improved_resume_filename)
            updated_doc.save(improved_resume_path)
            st.session_state["optimized_resume_path"] = improved_resume_path

            # === Cover Letter Generation ===
            cover_letter_text = generate_cover_letter(resume_text, jd_text, api_key)

            cover_doc = docx.Document()
            cover_doc.add_paragraph(cover_letter_text)
            style = cover_doc.styles['Normal']
            font = style.font
            font.name = 'Arial'
            font.size = Pt(11)

            cover_letter_filename = f"Cover_Letter_{candidate_name}_{company_name}.docx"
            cover_letter_path = os.path.join(tempfile.gettempdir(), cover_letter_filename)
            cover_doc.save(cover_letter_path)

            st.session_state["optimized_cover_letter_path"] = cover_letter_path

# === Display Results if available ===
if st.session_state["gpt_result"]:
    st.subheader("GPT ATS Analysis Output")
    st.text_area("Raw Output", value=st.session_state["gpt_result"], height=400)

    if st.session_state["optimized_resume_path"]:
        resume_filename = f"Luiz_Resume_{st.session_state['company_name']}_v2.docx"
        st.download_button(
            "Download Optimized Resume",
            open(st.session_state["optimized_resume_path"], "rb"),
            file_name=resume_filename
        )

    if st.session_state["optimized_cover_letter_path"]:
        cover_filename = f"Cover_Letter_{st.session_state['candidate_name']}_{st.session_state['company_name']}.docx"
        st.download_button(
            "Download Cover Letter",
            open(st.session_state["optimized_cover_letter_path"], "rb"),
            file_name=cover_filename
        )
