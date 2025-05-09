# gpt_helper_work_version.py (v1.3) – JSON prompt optimized

from openai import OpenAI

def get_resume_analysis(resume_text, jd_text, api_key, include_replacements=False):
    client = OpenAI(api_key=api_key)

    base_prompt = (
        "Act as an Applicant Tracking System (ATS) used by a hiring company.\n"
        "Compare the uploaded resume with the job description (JD) provided and simulate a full ATS screening and optimization process.\n\n"

        "Perform the following steps:\n\n"

        "1️⃣ Parse Resume Content:\n"
        "- Contact Information\n"
        "- Professional Summary\n"
        "- Work Experience\n"
        "- Education\n"
        "- Skills and Tools\n"
        "- Certifications and Languages\n\n"

        "2️⃣ Parse Job Description (JD):\n"
        "- Company Name\n"
        "- Job Title\n"
        "- Name, phone, email of the recruiter\n"
        "- Job location (If there are multiple locations, choose the nearest to the resume information)\n"
        "- Required Skills and Keywords\n"
        "- Responsibilities\n"
        "- Preferred Qualifications and Experience\n"
        "- Salary range\n"
        "- Relocation support (If not mentioned, answer with NM)\n"
        "- Is it required US Citizen or Permanent Resident? (If not mentioned, answer with NM)\n"
        "- Is Licensed Professional Engineer, PE or P.E. required? (If not mentioned, answer with Not required)\n\n"

        "3️⃣ Resume Evaluation:\n"
        "- Match hard and soft skills (consider frequency/context)\n"
        "- Job title and role alignment\n"
        "- Years and scope of experience\n"
        "- Education compatibility\n"
        "- Licensed Professional Engineer, PE or P.E. if it is required.\n"
        "- Date formatting and structure\n"
        "- ATS-friendly formatting compliance\n\n"

        "4️⃣ Red Flag Detection:\n"
        "- Employment gaps\n"
        "- Missing section headers\n"
        "- Keyword stuffing\n"
        "- Licensed Professional Engineer, PE or P.E. if required and missing\n"
        "- US Citizenship requirement if missing\n"
        "- Vague or irrelevant job titles\n\n"

        "5️⃣ Scoring:\n"
        "- Assign an ATS compatibility score (0–100%) based on:\n"
        "  - Keyword match\n"
        "  - Role and title alignment\n"
        "  - Skill/tool match\n"
        "  - Licensed Professional Engineer, PE or P.E. if it is required (if missing, consider no fit)\n"
        "  - Education relevance\n"
        "  - Formatting compliance\n\n"

        "6️⃣ Resume Improvement Suggestions:\n"
        "- Suggest replacements or additions to better align with the JD\n"
        "- Do not invent or assume experience\n"
        "- Reframe existing experience using similar language\n"
        "- List the 5 experiences and skills that are irrelevant to the position described in the resume\n"
        "- For each suggestion, include:\n"
        "   - 'Was': the original phrase\n"
        "   - 'New': the improved phrase\n"
        "   - 'Section': which resume section it came from\n"
        "- Try to classify into:\n"
        "   - Head (Candidate personal information)\n"
        "   - Target Position\n"
        "   - Professional Profile\n"
        "   - Expertises\n"
        "   - Accomplishments\n"
        "   - Career Experience\n"
        "   - Skills\n"
        "   - Certifications\n"
        "   - Education\n"
        "   - Others (fallback if unknown)\n\n"

        "7️⃣ Generate a New Optimized Resume:\n"
        "- ATS-compliant formatting\n"
        "- Standard section headers, no tables or graphics\n"
        "- Consistent date formats\n"
        "- Use a clear, professional tone\n"
        "- Do not introduce untrue information\n\n"

        "8️⃣ Return the Output As:\n"
        "- ✅ Compatibility Score (original and optimized)\n"
        "- ✅ Summary of matched and missing skills\n"
        "- ✅ Change Log (Was → New) in JSON format with Section\n"
        "- ✅ Resume improvement rationale\n"
        "- ✅ Final optimized resume text\n\n"

        "9️⃣ Suggest Improvements Breakdown:\n"
        "- List missing and underused keywords\n"
        "- Suggest sentence rewrites per section\n"
        "- Highlight formatting and structural ATS issues\n"
        "- Provide summary and rationale\n"

        "🔟 Return Final Output Structure:\n"
        "- 'ResumeContent': parsed resume information\n"
        "- 'JobDescription': parsed JD fields\n"
        "- 'ResumeEvaluation': all ATS alignment factors\n"
        "- 'RedFlagDetection': detected resume risks\n"
        "- 'Scoring': detailed scoring breakdown\n"
        "- 'ResumeImprovementSuggestions': full change log with Was/New/Section\n"
        "- 'NewOptimizedResume': ATS rewritten resume text (string format)\n"
        "- 'Output':\n"
        "  - 'CompatibilityScoreOriginal': original resume score\n"
        "  - 'CompatibilityScoreOptimized': after improvements\n"
        "  - 'SummaryOfMatchedAndMissingSkills': list\n"
        "  - 'ChangeLog': list of {'Was', 'New', 'Section'}\n"
        "  - 'ResumeImprovementRationale': explanation\n"
        "  - 'FinalOptimizedResumeText': final text-only resume\n"
        "- 'ImprovementsBreakdown':\n"
        "  - 'MissingAndUnderusedKeywords': list\n"
        "  - 'SentenceRewritesPerSection': list\n"
        "  - 'FormattingAndStructuralATSIssues': notes\n"
        "  - 'SummaryAndRationale': overview justification\n\n"

        "✅ Return ONLY a single valid JSON object using the exact key names above. Do not include any explanations or markdown. Use double quotes for all keys and string values."
    )

    if prompt_instructions:
        base_prompt += f"\n\n{prompt_instructions}"

    full_prompt = (
        f"{base_prompt}\n\n"
        f"Job Description:\n{jd_text}\n\n"
        f"Resume:\n{resume_text}\n"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional ATS resume assistant."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.2,
            top_p=1.0,
            max_tokens=4000
        )
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error contacting OpenAI: {str(e)}"

# === Function to generate cover letter avoiding direct company mention ===
def generate_cover_letter(resume_text, jd_text, api_key):
    client = OpenAI(api_key=api_key)

    prompt = (
        "Generate a professional Cover Letter based on the provided Resume and Job Description.\n"
        "Constraints:\n"
        "- Do NOT directly mention the Company name from the Job Description.\n"
        "- Refer generically to 'this opportunity', 'this position', or 'your organization'.\n"
        "- Focus on matching the candidate's skills with the position requirements.\n"
        "- Maintain a professional and engaging tone.\n"
        "- Do not invent or add experiences not present in the resume.\n"
        "- Make the cover letter concise and compelling.\n\n"
        f"Job Description:\n{jd_text}\n\nResume:\n{resume_text}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional career assistant generating compelling cover letters."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating cover letter: {str(e)}"
