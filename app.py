# ========================================
# ATS Resume Optimizer WebApp - Version v1.3.2
# ========================================

import streamlit as st
import os
import io
import pytz
import openai
import base64
import zipfile
import datetime

from docx import Document
from gpt_helper_work_version import get_resume_analysis
from main_work_version_1_01_updated import (
    extract_text,
    extract_candidate_name,
    extract_company_name_from_gpt_output,
    extract_job_title_from_gpt_output,
    download_word_file,
    generate_short_candidate_code,
    generate_short_company_code,
    load_or_create_tracker,
    update_resume_tracker,
    update_jd_tracker,
    update_change_log,
)

# ========== App UI Configuration ==========

st.set_page_config(
    page_title="ATS Resume Optimizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("# :mag: ATS Resume Optimizer v1.3.2")
st.markdown("### Optimize your resume for any job description and track your progress automatically.")

# ========== Sidebar Inputs ==========

with st.sidebar:
    st.header("🔧 Setup & Inputs")

    # User Info
    user_id = st.text_input("User ID (Initials or Code)", max_chars=12, help="Required to create your personal tracking log.")
    openai_key = st.text_input("OpenAI API Key", type="password", help="Paste your OpenAI key here.")
    timezone = st.selectbox("Select Timezone", ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles"], index=1)

    # File Uploads
    uploaded_resume = st.file_uploader("📄 Upload Resume (.docx or .pdf)", type=["docx", "pdf"], help="Upload your resume file to analyze.")
    uploaded_jd = st.file_uploader("📄 Upload Job Description (.docx or .pdf)", type=["docx", "pdf"], help="Upload the job description.")
    uploaded_tracker = st.file_uploader("📊 Optional: Upload existing Tracker (.xlsx)", type=["xlsx"], help="Optional. Continue logging into an existing report.")

    # Optional Fields
    company_name_input = st.text_input("Company Name (Optional)", help="Leave blank to auto-extract from Job Description.")

    # Tips
    st.info("💡 **Tips:**\n- Fill in your User ID before starting.\n- The app will create a personalized Excel tracker file for you.\n- If you’re using this for the first time, no need to upload a tracker — one will be created automatically.")

# ========== Resume Optimization Trigger ==========

if st.button("🚀 Run Resume Optimization"):

    # === Validation ===
    if not all([user_id, openai_key, uploaded_resume, uploaded_jd]):
        st.warning("Please complete all required fields: User ID, API Key, Resume, and Job Description.")
        st.stop()

    # === Load Files ===
    resume_text = extract_text(uploaded_resume)
    jd_text = extract_text(uploaded_jd)

    # === GPT Analysis ===
    try:
        gpt_result = get_resume_analysis(resume_text, jd_text, openai_key, include_replacements=True)
    except Exception as e:
        st.error(f"Error contacting OpenAI: {e}")
        st.stop()

    # === Extract Details from GPT ===
    candidate_name = extract_candidate_name(resume_text)
    company_name = company_name_input.strip() or extract_company_name_from_gpt_output(gpt_result)
    job_title = extract_job_title_from_gpt_output(gpt_result)

    # === Timestamp and File Naming ===
    tz = pytz.timezone(timezone)
    now = datetime.datetime.now(tz)
    timestamp = now.strftime("%y%m%d-%H%M")
    candidate_code = generate_short_candidate_code(candidate_name)
    company_code = generate_short_company_code(company_name)

    # === File Names ===
    base_filename = f"{candidate_code}_{company_code}_{timestamp}"
    resume_filename = f"Resume_{base_filename}.docx"
    cl_filename = f"Cover_Letter_{base_filename}.docx"

    # === Save Resume & Cover Letter ===
    improved_resume = gpt_result.get("Final Optimized Resume", "")
    cover_letter = gpt_result.get("Cover Letter", "")
    download_word_file(improved_resume, resume_filename)
    download_word_file(cover_letter, cl_filename)

    # === Show Outputs ===
    st.success("✅ Analysis Completed!")
    st.markdown(f"**Candidate:** {candidate_name}")
    st.markdown(f"**Company:** {company_name}")
    st.markdown(f"**Job Title:** {job_title}")
    st.markdown(f"**Compatibility Score:** {gpt_result.get('Compatibility Score', 'N/A')}%")

    st.download_button("📥 Download Improved Resume", improved_resume.encode(), file_name=resume_filename)
    st.download_button("📥 Download Cover Letter", cover_letter.encode(), file_name=cl_filename)

    # === Analysis Summary ===
    with st.expander("🔍 Detailed GPT Analysis"):
        st.write(gpt_result)

    # === Update Tracker ===
    if user_id:
        tracker_filename = f"Resume_Job_Tracker_{user_id.upper()}.xlsx"
        workbook, jd_tracker, resume_tracker, change_log = load_or_create_tracker(tracker_filename, uploaded_tracker)

        jd_id = update_jd_tracker(jd_tracker, job_title, company_name, now)
        update_resume_tracker(resume_tracker, resume_filename, job_title, gpt_result, now, jd_id)
        update_change_log(change_log, uploaded_resume.name, resume_filename, gpt_result.get("Change Log", []), jd_id)

        # Save updated Excel
        workbook.save(tracker_filename)
        with open(tracker_filename, "rb") as f:
            st.download_button("📊 Download Tracker", f, file_name=tracker_filename)

# ========== Footer ==========
st.markdown("---")
st.caption("ATS Resume Optimizer v1.3.2 • Built with ❤️ and GPT-4 • Developed by Luiz Segatti")
