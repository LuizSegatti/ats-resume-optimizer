# Resume Matcher App – GPT-Based Analysis, Resume Rewriter, and Excel Logger
# import PySimpleGUI as sg "Not more necessary for Web applications"
import streamlit as st
import fitz  # PyMuPDF
import docx
import os
import re
import openpyxl
from datetime import datetime
from gpt_helper_work_version import get_resume_analysis, generate_cover_letter
from dotenv import load_dotenv
import time
import tempfile

# Load API Key from .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# === Folder Paths (Windows-Compatible) ===
BASE_FOLDER = os.path.join(os.environ["USERPROFILE"], "OneDrive", "Job_Follow-up")
RESUME_FOLDER = os.path.join(BASE_FOLDER, "01-Base_Resumes")
JD_FOLDER = os.path.join(BASE_FOLDER, "02-Job_Descriptions")
OUTPUT_FOLDER = os.path.join(BASE_FOLDER, "03-Customized_Resumes")
COVER_FOLDER = os.path.join(BASE_FOLDER, "06-Cover Letter")
TRACKER_PATH = os.path.join(BASE_FOLDER, "04-Reports", "ResumeTracker_1_2.xlsx")

# === Custom Cover Letter Support ===
def extract_candidate_name(resume_text):
    match = re.search(r"(?i)^\s*([A-Z][a-z]+\s+[A-Z][a-z]+.*)", resume_text)
    return match.group(1).strip() if match else "Candidate"

def extract_candidate_info(resume_text):
    info = {}
    name_match = re.search(r"(?i)^\s*([A-Z][a-z]+\s+[A-Z][a-z]+.*)", resume_text)
    email_match = re.search(r"[\w.-]+@[\w.-]+", resume_text)
    phone_match = re.search(r"(\(\d{3}\)\s*\d{3}-\d{4})|(\d{3}-\d{3}-\d{4})", resume_text)
    location_match = re.search(r"(?i)\b(Mount Pleasant,\s*TX)\b", resume_text)

    if name_match:
        info["[Name]"] = name_match.group(1).strip()
    if email_match:
        info["[Email]"] = email_match.group(0).strip()
    if phone_match:
        info["[Phone]"] = phone_match.group(0).strip()
    if location_match:
        info["[Location]"] = location_match.group(1).strip()

    return info

# === Save Customized Cover Letter ===

def save_customized_cover_letter(template_path, output_folder, cover_text, resume_text, company_name):
    from docx import Document
    from datetime import datetime
    import os
    import re

    candidate_info = {}

    # Extract candidate data using regex
    name_match = re.search(r"^\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", resume_text, re.MULTILINE)
    email_match = re.search(r"[\w\.-]+@[\w\.-]+", resume_text)
    phone_match = re.search(r"(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})", resume_text)
    linkedin_match = re.search(r"(https?://(www\.)?linkedin\.com/in/[\w\d-]+)", resume_text)
    city_state_match = re.search(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z]{2})\b", resume_text)

    if name_match:
        candidate_info["[Candidate Name]"] = name_match.group(1).strip()
    if email_match:
        candidate_info["[candidate email]"] = email_match.group(0).strip()
    if phone_match:
        digits = re.sub(r"\D", "", phone_match.group(0))
        if len(digits) == 10:
            candidate_info["[candidate phone]"] = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    if linkedin_match:
        candidate_info["[LinkedIn]"] = linkedin_match.group(1).strip()
    if city_state_match:
        candidate_info["[candidate city, State]"] = city_state_match.group(1).strip()

    candidate_info["[date]"] = datetime.today().strftime("%B %d, %Y")

    doc = Document(template_path)

    for para in doc.paragraphs:
        for run in para.runs:
            for placeholder, value in candidate_info.items():
                if placeholder in run.text:
                    run.text = run.text.replace(placeholder, value)

    # Replace [InsertCoverLetterHere] paragraph with GPT text
    for i, para in enumerate(doc.paragraphs):
        if "[InsertCoverLetterHere]" in para.text:
            style = para.style
            doc.paragraphs[i]._element.clear_content()
            for line in cover_text.strip().splitlines():
                new_para = doc.paragraphs[i].insert_paragraph_before(line.strip())
                new_para.style = style
            break

    candidate_name = candidate_info.get("[Candidate Name]", "Candidate")
    filename = f"CV_{candidate_name}-{company_name}-{datetime.today().strftime('%Y-%m-%d')}.docx"
    filepath = os.path.join(output_folder, filename)
    doc.save(filepath)
    return filepath, candidate_name


def extract_text(file_path):
    if file_path.lower().endswith(".pdf"):
        doc = fitz.open(file_path)
        text = "\n".join([page.get_text() for page in doc])
        doc.close()
        return text
    elif file_path.lower().endswith(".docx"):
        while True:
            try:
                return "\n".join([p.text for p in docx.Document(file_path).paragraphs])
            except Exception:
                raise Exception(f"Please make sure the file is not open: {file_path}")
    return ""

# === Replacements Parser ===
import json
def parse_replacements(gpt_output):
    json_block = re.search(r"```json\s*(\[.*?\])\s*```", gpt_output, re.DOTALL)
    if json_block:
        try:
            replacements = json.loads(json_block.group(1))
            return [(item["was"], item["new"], item.get("section", "Unknown")) for item in replacements]
        except Exception as e:
            print("⚠️ Failed to parse JSON change log:", e)
            return []
    return re.findall(r"(?i)replace [“\"](.+?)[”\"] with [“\"](.+?)[”\"]", gpt_output)

# === Apply Replacements to Resume ===
def apply_replacements_to_docx(original_path, replacements):
    while True:
        try:
            doc = docx.Document(original_path)
            break
        except Exception:
            st.warning(f"⚠️ Please close the resume file:\n{original_path}")
            time.sleep(1)
    changes = []
    for para in doc.paragraphs:
        for old, new in replacements:
            if old.lower() in para.text.lower():
                pattern = re.compile(re.escape(old), re.IGNORECASE)
                updated_text = pattern.sub(new, para.text)
                if updated_text != para.text:
                    para.text = updated_text
                    changes.append((old, new, "Resume Body"))
    return doc, changes

# === Extract Optimized Resume ===
def extract_final_resume_text(gpt_output):
    block = re.search(r"(?:## Final optimized resume|```text)(.*?)(?:```|\Z)", gpt_output, re.DOTALL | re.IGNORECASE)
    if block:
        return block.group(1).strip()
    return None

# === Extract Company Name from GPT ===
def extract_company_name_from_gpt(gpt_output):
    match = re.search(r"(?i)Company(?: Name)?:\s*(.+)", gpt_output)
    if match:
        return match.group(1).strip()
    return "UnknownCompany"

# === Excel Logging ===
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table

def log_gpt_results(tracker_path, resume_name, jd_name, score, changes, resume_filename, company_name):
    from datetime import datetime
    import time

    wb = None
    while wb is None:
        try:
            wb = openpyxl.load_workbook(tracker_path)
        except PermissionError:
            st.warning("⚠️ Please close the Excel file before continuing.")
            time.sleep(1)

    try:
        today = datetime.today()
        job_title = jd_name.replace(".docx", "")
        resume_version = resume_filename.replace(".docx", "")

        def format_score(score_text):
            try:
                return float(score_text.replace('%', '').strip()) / 100
            except:
                return None

        # === ATS_Report_Log ===
        ats = wb["ATS_Report_Log"]
        ats_table = ats.tables["ATS_Report"]
        ats.append([
            ats.max_row,
            resume_version,
            job_title,
            company_name,
            format_score(score),
            f"{len(changes)} changes",
            today.date()
        ])
        # Expand the table to include the new row
        ats_table.ref = f"A1:{get_column_letter(ats.max_column)}{ats.max_row}"

        # === Change_Log ===
        chg = wb["Change_Log"]
        chg_table = chg.tables["Change_Log"]
        for old, new, section in changes:
            chg.append([
                chg.max_row,
                resume_version,
                old,
                new,
                section,
                job_title,
                today.date()
            ])
        chg_table.ref = f"A1:{get_column_letter(chg.max_column)}{chg.max_row}"

        # === Resume_Inventory ===
        inv = wb["Resume_Inventory"]
        inv_table = inv.tables["Resume_Inventory"]
        inv.append([
            resume_version,
            resume_name,
            job_title,
            f"/03-Customized_Resumes/{resume_filename}",
            today.date()
        ])
        inv_table.ref = f"A1:{get_column_letter(inv.max_column)}{inv.max_row}"

        # === Job_Application_Tracker (if exists) ===
        if "Job_Application_Tracker" in wb.sheetnames:
            tracker = wb["Job_Application_Tracker"]
            tracker_table = tracker.tables["tblJobApplications"]
            tracker.append([
                tracker.max_row,
                resume_version,
                job_title,
                company_name,
                today.date(),
                "Pending",
                "Auto-logged"
            ])
            tracker_table.ref = f"A1:{get_column_letter(tracker.max_column)}{tracker.max_row}"

        wb.save(tracker_path)

    finally:
        wb.close()


# === GUI Layout ===
layout = [
    [sg.Text("Resume File"), sg.Input(default_text=RESUME_FOLDER, key="-RESUME-"), sg.FileBrowse("Browse", target="-RESUME-", initial_folder=RESUME_FOLDER)],
    [sg.Text("Job Description File"), sg.Input(default_text=JD_FOLDER, key="-JD-"), sg.FileBrowse("Browse", target="-JD-", initial_folder=JD_FOLDER)],
    [sg.Text("ResumeTracker.xlsx"), sg.Input(default_text=TRACKER_PATH, key="-TRACKER-"), sg.FileBrowse("Browse", target="-TRACKER-", initial_folder=os.path.dirname(TRACKER_PATH))],
    [sg.Text("Company Name (leave blank to auto-detect)")],
    [sg.Input(key="-COMPANY-")],
    [sg.Button("Analyze"), sg.Button("Exit")],
    [sg.Text("GPT ATS Analysis Output:")],
    [sg.Multiline("", key="-GPT-RESULT-", size=(100, 40), autoscroll=True)]
]

window = sg.Window("Resume & JD Auto-Matcher (ChatGPT Enabled)", layout)

# === Main App Loop ===
    if event == "Analyze":
        resume_path, jd_path, tracker_path = values["-RESUME-"], values["-JD-"], values["-TRACKER-"]
        if not (resume_path and jd_path and tracker_path):
            sg.popup("Please fill in all fields (Resume, JD, Tracker). Company name is optional.")
            continue

        resume_text, jd_text = extract_text(resume_path), extract_text(jd_path)
        try:
            gpt_result = get_resume_analysis(
                resume_text,
                jd_text,
                api_key,
                include_replacements=True
            )

            # Update Output Field
            window["-GPT-RESULT-"].update(gpt_result)

            # Extract company name from GPT output
            company_input = values["-COMPANY-"].strip()
            company_name = company_input if company_input else extract_company_name_from_gpt(gpt_result)

            # Extract change log and apply to original resume
            replacements = parse_replacements(gpt_result)
            edited_doc, changes = apply_replacements_to_docx(resume_path, replacements)

            # Extract optimized resume (if found) and overwrite Word output
            optimized_text = extract_final_resume_text(gpt_result)
            resume_filename = f"Luiz_Resume_{company_name}_v2.docx"
            out_path = os.path.join(OUTPUT_FOLDER, resume_filename)

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

            # Log everything
            log_gpt_results(tracker_path, os.path.basename(resume_path), os.path.basename(jd_path), score, changes, resume_filename, company_name)

            # === Generate and Save Cover Letter ===
            cover_letter_text = generate_cover_letter(resume_text, jd_text, api_key)
            cover_path, candidate_name = save_customized_cover_letter(
                template_path=os.path.join(BASE_FOLDER, "01-Base_Resumes", "Cover_Letter_Template.docx"),
                output_folder=os.path.join(BASE_FOLDER, "06-Cover Letter"),  # ✅ correct save location
                cover_text=cover_letter_text,
                resume_text=resume_text,
                company_name=company_name
            )

            st.success(f"✅ Analysis complete!\nSaved as '{resume_filename}' and logged in Excel.\n📄 Cover letter saved to:\n{cover_path}")

        except Exception as e:
            st.error(f"ChatGPT analysis failed: {str(e)}")


window.close()
