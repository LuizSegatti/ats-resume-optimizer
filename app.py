import streamlit as st
import os
import re
import fitz  # PyMuPDF
import tempfile
import docx
from docx.shared import Pt
from datetime import datetime
import pytz
from gpt_helper_work_version import get_resume_analysis, generate_cover_letter
from main_work_version_1_01_updated import extract_text, apply_replacements_to_docx

# === Initialize session state variables ===
for key in ["gpt_result", "optimized_resume_path", "optimized_cover_letter_path", "company_name", "candidate_name", "replacements"]:
    if key not in st.session_state:
        st.session_state[key] = None

# === Page config and title ===
st.set_page_config(page_title="ATS Resume Optimizer", layout="wide")
st.title("📄 ATS Resume Optimizer v1.1.1 – GPT Enhanced")

# === Timezone Selection ===
timezone_options = {
    "Central Time (America/Chicago)": "America/Chicago",
    "Eastern Time (America/New_York)": "America/New_York",
    "Mountain Time (America/Denver)": "America/Denver",
    "Pacific Time (America/Los_Angeles)": "America/Los_Angeles"
}
selected_timezone = st.selectbox(
    "Select your Time Zone:",
    options=list(timezone_options.keys()),
    index=0
)
local_tz = pytz.timezone(timezone_options[selected_timezone])

# === Upload Section ===
st.subheader("Upload Files")
uploaded_resume = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx"], key="resume")
uploaded_jd = st.file_uploader("Upload Job Description (PDF/DOCX)", type=["pdf", "docx"], key="jd")
company_name_input = st.text_input("Company Name (optional)")
api_key = st.text_input("Enter your OpenAI API Key:", type="password")

analyze_btn = st.button("Analyze Resume")

# === Helper Functions ===
def parse_replacements_from_output(gpt_output):
    try:
        matches = re.findall(r'Replace \"(.*?)\" with \"(.*?)\"', gpt_output)
        return matches
    except Exception:
        return []

def extract_candidate_name_from_resume(resume_text):
    lines = resume_text.split('\n')
    for line in lines:
        cleaned = line.strip()
        if cleaned and len(cleaned.split()) >= 2:
            return cleaned
    return "UnknownCandidate"

def extract_company_name_from_jd(jd_text):
    company_line = re.search(r'Company:\s*(.*)', jd_text, re.IGNORECASE)
    if company_line:
        return company_line.group(1).strip()
    patterns = [
        r'About\s+(.*?)\s+is\s+a',
        r'Join\s+(.*?)\s+as',
        r'work\s+at\s+(.*?)\s+\(',
        r'careers\s+at\s+(.*?)\s+'
    ]
    for pattern in patterns:
        match = re.search(pattern, jd_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "UnknownCompany"

# === Main App Flow ===
if analyze_btn and uploaded_resume and uploaded_jd and api_key:
    ext_resume = uploaded_resume.name.lower()
    ext_jd = uploaded_jd.name.lower()
    if not ext_resume.endswith(".docx") or not ext_jd.endswith(".docx"):
        st.error("Resume and Job Description must both be DOCX files. Please upload .docx files.")
    else:
        with st.spinner("Extracting and analyzing..."):

            # Save Uploaded Resume and JD to Temp Files
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_resume:
                tmp_resume.write(uploaded_resume.getbuffer())
                resume_path = tmp_resume.name

            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_jd:
                tmp_jd.write(uploaded_jd.getbuffer())
                jd_path = tmp_jd.name

            # Extract Texts
            resume_text = extract_text(resume_path)
            jd_text = extract_text(jd_path)

            # GPT Resume Analysis
            gpt_result = get_resume_analysis(resume_text, jd_text, api_key, include_replacements=True)
            st.session_state["gpt_result"] = gpt_result

            # Parse Replacements
            replacements = parse_replacements_from_output(gpt_result)
            st.session_state["replacements"] = replacements

            # Candidate and Company Name
            company_name = company_name_input.strip()
            if not company_name:
                company_name = extract_company_name_from_jd(jd_text)
            st.session_state["company_name"] = company_name

            candidate_name = extract_candidate_name_from_resume(resume_text)
            st.session_state["candidate_name"] = candidate_name

            # Short Name Creation
            candidate_short = ''.join([word[0] for word in candidate_name.split() if word])
            company_words = company_name.split()
            company_short = '_'.join(company_words[:2]) if len(company_words) >= 2 else company_name.replace(' ', '_')

            # Local Timestamp
            timestamp = datetime.now(local_tz).strftime("%y%m%d-%H%M")

            # Resume Improvement
            resume_filename = f"Resume_{candidate_short}_{company_short}_{timestamp}.docx"
            improved_resume_path = os.path.join(tempfile.gettempdir(), resume_filename)

            updated_doc, changes = apply_replacements_to_docx(resume_path, replacements)
            updated_doc.save(improved_resume_path)
            st.session_state["optimized_resume_path"] = improved_resume_path

            # Cover Letter Generation
            cover_letter_text = generate_cover_letter(resume_text, jd_text, api_key)
            cover_letter_filename = f"Cover_Letter_{candidate_short}_{company_short}_{timestamp}.docx"
            cover_letter_path = os.path.join(tempfile.gettempdir(), cover_letter_filename)

            cover_doc = docx.Document()
            cover_doc.add_paragraph(cover_letter_text)
            style = cover_doc.styles['Normal']
            font = style.font
            font.name = 'Arial'
            font.size = Pt(11)
            cover_doc.save(cover_letter_path)
            st.session_state["optimized_cover_letter_path"] = cover_letter_path

# === Results Display ===
if st.session_state["gpt_result"]:
    st.subheader("GPT ATS Analysis Output")
    st.text_area("Raw Output", value=st.session_state["gpt_result"], height=400)

if st.session_state["optimized_resume_path"]:
    st.download_button(
        "Download Optimized Resume",
        open(st.session_state["optimized_resume_path"], "rb"),
        file_name=os.path.basename(st.session_state["optimized_resume_path"])
    )

if st.session_state["optimized_cover_letter_path"]:
    st.download_button(
        "Download Cover Letter",
        open(st.session_state["optimized_cover_letter_path"], "rb"),
        file_name=os.path.basename(st.session_state["optimized_cover_letter_path"])
    )
