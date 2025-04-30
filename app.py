import streamlit as st
import os
import re
import fitz  # PyMuPDF
import tempfile
import docx
from docx.shared import Pt
from datetime import datetime
import pytz
import pandas as pd
from openpyxl import Workbook
from io import BytesIO
from gpt_helper_work_version import get_resume_analysis, generate_cover_letter
from main_work_version_1_01_updated import extract_text, apply_replacements_to_docx

# === App Version Title ===
st.set_page_config(page_title="ATS Resume Optimizer", layout="wide")
st.title("📄 ATS Resume Optimizer v1.2 – GPT Enhanced + Tracker")

# === Initialize session state variables ===
for key in ["gpt_result", "optimized_resume_path", "optimized_cover_letter_path", "company_name", "candidate_name", "replacements"]:
    if key not in st.session_state:
        st.session_state[key] = None

# === Timezone Selection ===
timezone_options = {
    "Central Time (America/Chicago)": "America/Chicago",
    "Eastern Time (America/New_York)": "America/New_York",
    "Mountain Time (America/Denver)": "America/Denver",
    "Pacific Time (America/Los_Angeles)": "America/Los_Angeles"
}
selected_timezone = st.selectbox("Select your Time Zone:", options=list(timezone_options.keys()), index=0)
local_tz = pytz.timezone(timezone_options[selected_timezone])

# === Tracker System Sidebar ===
st.sidebar.header("🔖 Tracker Management")

uploaded_tracker = st.sidebar.file_uploader("Upload Existing Tracker (Optional)", type=["xlsx"])
tracker_user_id = None
jd_tracker = None
resume_tracker = None
change_log_tracker = None

if uploaded_tracker:
    try:
        xls = pd.ExcelFile(uploaded_tracker)
        jd_tracker = pd.read_excel(xls, sheet_name="JD_Analysis")
        resume_tracker = pd.read_excel(xls, sheet_name="Resume_Tracker")
        change_log_tracker = pd.read_excel(xls, sheet_name="Resume_Change_Log")
        tracker_filename = uploaded_tracker.name
        st.sidebar.success(f"✅ Loaded existing Tracker: {tracker_filename}")
    except Exception as e:
        st.sidebar.error(f"❌ Error loading Tracker file: {e}")
else:
    tracker_user_id = st.sidebar.text_input("New User: Enter Personal Tracker ID", value="")
    if tracker_user_id:
        tracker_filename = f"Resume_Job_Tracker_{tracker_user_id}.xlsx"
        jd_tracker = pd.DataFrame(columns=["ID#", "JD Title", "Company", "Analysis Date"])
        resume_tracker = pd.DataFrame(columns=["ID#", "Resume File Name", "JD Title", "Match in %", "Summary of Changes", "Created Date"])
        change_log_tracker = pd.DataFrame(columns=["ID#", "Original Resume File Name", "Resume File Name", "Was", "New", "Section", "JD Title"])
    else:
        tracker_filename = None

# === Helper Functions ===
def generate_new_id(df):
    if df is None or df.empty:
        return 1
    else:
        return int(df["ID#"].max()) + 1

def generate_excel_download(jd_df, resume_df, change_log_df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        jd_df.to_excel(writer, sheet_name="JD_Analysis", index=False)
        resume_df.to_excel(writer, sheet_name="Resume_Tracker", index=False)
        change_log_df.to_excel(writer, sheet_name="Resume_Change_Log", index=False)
    return output.getvalue()

def parse_replacements_from_output(gpt_output):
    try:
        return re.findall(r'Replace \"(.*?)\" with \"(.*?)\"', gpt_output)
    except:
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
    # === Upload Section ===
st.subheader("Upload Files")
uploaded_resume = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx"], key="resume")
uploaded_jd = st.file_uploader("Upload Job Description (PDF/DOCX)", type=["pdf", "docx"], key="jd")
company_name_input = st.text_input("Company Name (optional)")
api_key = st.text_input("Enter your OpenAI API Key:", type="password")
analyze_btn = st.button("Analyze Resume")

# === Main App Flow ===
if analyze_btn and uploaded_resume and uploaded_jd and api_key:
    ext_resume = uploaded_resume.name.lower()
    ext_jd = uploaded_jd.name.lower()
    if not ext_resume.endswith(".docx") or not ext_jd.endswith(".docx"):
        st.error("Resume and Job Description must both be DOCX files. Please upload .docx files.")
    else:
        with st.spinner("Extracting and analyzing..."):

            # === Save Uploaded Files to Temp Paths ===
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_resume:
                tmp_resume.write(uploaded_resume.getbuffer())
                resume_path = tmp_resume.name

            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_jd:
                tmp_jd.write(uploaded_jd.getbuffer())
                jd_path = tmp_jd.name

            # === Extract Text ===
            resume_text = extract_text(resume_path)
            jd_text = extract_text(jd_path)

            # === GPT Analysis ===
            gpt_result = get_resume_analysis(resume_text, jd_text, api_key, include_replacements=True)
            st.session_state["gpt_result"] = gpt_result
            replacements = parse_replacements_from_output(gpt_result)
            st.session_state["replacements"] = replacements

            # === Identify Company and Candidate ===
            company_name = company_name_input.strip() or extract_company_name_from_jd(jd_text)
            st.session_state["company_name"] = company_name
            candidate_name = extract_candidate_name_from_resume(resume_text)
            st.session_state["candidate_name"] = candidate_name

            # === Short Name & Timestamp for Filenames ===
            candidate_short = ''.join([word[0] for word in candidate_name.split() if word])
            company_words = company_name.split()
            company_short = '_'.join(company_words[:2]) if len(company_words) >= 2 else company_name.replace(' ', '_')
            timestamp = datetime.now(local_tz).strftime("%y%m%d-%H%M")
            # === Generate Resume Filename and Save Updated Resume ===
            resume_filename = f"Resume_{candidate_short}_{company_short}_{timestamp}.docx"
            improved_resume_path = os.path.join(tempfile.gettempdir(), resume_filename)
            updated_doc, changes = apply_replacements_to_docx(resume_path, replacements)
            updated_doc.save(improved_resume_path)
            st.session_state["optimized_resume_path"] = improved_resume_path

            # === Generate Cover Letter ===
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
            # === Tracker Update Block ===
            if tracker_filename:
                # JD Tracker
                jd_id = generate_new_id(jd_tracker)
                jd_title = f"{'_'.join(company_name.split()[:2])}_{gpt_result.split('Job Title:')[1].split('\n')[0].strip()}" if "Job Title:" in gpt_result else f"{'_'.join(company_name.split()[:2])}_UnknownTitle"
                analysis_date = datetime.now(local_tz).strftime("%m/%d/%y")
                jd_tracker.loc[len(jd_tracker)] = [jd_id, jd_title, company_name, analysis_date]

                # Resume Tracker
                resume_id = generate_new_id(resume_tracker)
                try:
                    match_line = next(line for line in gpt_result.splitlines() if "Compatibility Score" in line)
                    match_percent = int(''.join(filter(str.isdigit, match_line.split('%')[0])))
                except:
                    match_percent = "N/A"
                num_changes = len(replacements) if replacements else 0
                created_date = datetime.now(local_tz).strftime("%m/%d/%y")
                resume_tracker.loc[len(resume_tracker)] = [
                    resume_id,
                    os.path.basename(improved_resume_path),
                    jd_title,
                    match_percent,
                    num_changes,
                    created_date
                ]

                # Change Log
                change_id = generate_new_id(change_log_tracker)
                for old, new in replacements:
                    change_log_tracker.loc[len(change_log_tracker)] = [
                        change_id,
                        uploaded_resume.name,
                        os.path.basename(improved_resume_path),
                        old,
                        new,
                        "Resume Body",
                        jd_title
                    ]
                    change_id += 1

                # Offer Tracker for Download
                st.subheader("📥 Download Tracker")
                st.download_button(
                    label="Download Updated Tracker",
                    data=generate_excel_download(jd_tracker, resume_tracker, change_log_tracker),
                    file_name=tracker_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# === Display GPT Analysis Output ===
if st.session_state["gpt_result"]:
    st.subheader("GPT ATS Analysis Output")
    st.text_area("Raw Output", value=st.session_state["gpt_result"], height=400)

# === Download Buttons ===
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

