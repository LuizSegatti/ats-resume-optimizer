# gpt_helper_work_version.py (v1.2) – Optimized for ATS Resume Optimizer with Section Detection

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
        "- Relocation support\n"
        "- Is it required US Citizen or Permanent Resident?\n"
        "- Is Licensed Professional Engineer, PE or P.E. required? (If not mentioned, consider as no requirement)\n\n"

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

        "Return a single valid JSON object.\n" 
        "Do NOT use markdown formatting (no triple backticks).\n" 
        "Do NOT add any explanations or text outside the JSON.\n"
    )

    full_prompt = (
        f"{base_prompt}\n\n"
        f"Job Description:\n{jd_text}\n\n"
        f"Resume:\n{resume_text}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an API service that outputs ONLY valid JSON. Do not include markdown (no triple backticks), explanations, or formatting — return a clean JSON object only.\n"
                    )
                },
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.4,
            max_tokens=2500
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
