import streamlit as st
import os
import re
import docx
import fitz  # PyMuPDF
import tempfile
from datetime import datetime
from gpt_helper_work_version import get_resume_analysis, generate_cover_letter
from main_work_version_1_01_updated import (
    parse_replacements,
    apply_replacements_to_docx,
    extract_final_resume_text,
    extract_company_name_from_gpt,
    log_gpt_results,
    save_customized_cover_letter,
)

# Load OpenAI API Key
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

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

analyze_btn = st.button("Analyze Resume")

if analyze_btn and uploaded_resume and uploaded_jd:
    with st.spinner("Extracting and analyzing..."):
        resume_text = extract_text(uploaded_resume)
        jd_text = extract_text(uploaded_jd)

        gpt_result = get_resume_analysis(resume_text, jd_text, api_key, include_replacements=True)

        st.subheader("GPT ATS Analysis Output")
        st.text_area("Raw Output", value=gpt_result, height=400)

        # Detect company name
        company_name = company_name_input.strip() or extract_company_name_from_gpt(gpt_result)

        # Extract replacements
        replacements = parse_replacements(gpt_result)

        # Apply replacements to resume
        resume_file_path = os.path.join(tempfile.gettempdir(), uploaded_resume.name)
        with open(resume_file_path, "wb") as f:
            f.write(uploaded_resume.getbuffer())

        edited_doc, changes = apply_replacements_to_docx(resume_file_path, replacements)

        # Final optimized resume text
        optimized_text = extract_final_resume_text(gpt_result)
        resume_filename = f"Luiz_Resume_{company_name}_v2.docx"
        out_path = os.path.join(tempfile.gettempdir(), resume_filename)

        if optimized_text:
            doc = docx.Document()
            for line in optimized_text.splitlines():
                doc.add_paragraph(line.strip())
            doc.save(out_path)
        else:
            edited_doc.save(out_path)

        # Extract score
        score_match = re.search(r"compatibility score.*?(\d+\.?\d*)%", gpt_result, re.IGNORECASE)
        score = score_match.group(1) if score_match else "N/A"

        # Display Results
        st.success(f"✅ Compatibility Score: {score}% for {company_name}")
        st.download_button("Download Optimized Resume", open(out_path, "rb"), file_name=resume_filename)

        # Generate Cover Letter
        cover_letter_text = generate_cover_letter(resume_text, jd_text, api_key)
        cover_path, _ = save_customized_cover_letter(
            template_path = "Cover_Letter_Template.docx"
            output_folder=tempfile.gettempdir(),
            cover_text=cover_letter_text,
            resume_text=resume_text,
            company_name=company_name
        )

        st.download_button("Download Cover Letter", open(cover_path, "rb"), file_name=os.path.basename(cover_path))
