import openai

def get_resume_analysis(resume_text, jd_text, api_key, include_replacements=False, prompt_instructions=None):
    openai.api_key = api_key

    # Base GPT prompt
    base_prompt = (
        "Act as an Applicant Tracking System (ATS) used by a hiring company. "
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
        "- Relocation suppport\n"
        "- Is it required US Citzen or Permanent Resident? "
        "- Is Licensed Professional Engineer, PE or P.E. required? (If there isn't mentioned consider as no requirement)\n\n"

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
        "- Licensed Professional Engineer, PE or P.E. if it is required."
        "- US Citizen reuired:\n"
        "- Vague or irrelevant job titles\n\n"

        "5️⃣ Scoring:\n"
        "- Assign an ATS compatibility score (0–100%) based on:\n"
        "  - Keyword match\n"
        "  - Role and title alignment\n"
        "  - Skill/tool match\n"
        "  - Licensed Professional Engineer, PE or P.E. if it is required. (If required and isn't in the resume, consider no fit for the job)\n"
        "  - Education relevance\n"
        "  - Formatting compliance\n\n"

        "6️⃣ Resume Improvement Suggestions:\n"
        "- Suggest replacements or additions to better align with the JD\n"
        "- Do not invent or assume experience\n"
        "- Reframe existing experience using similar language\n"
        "- List the 5 experiences and skills that are irrelevant to the position described in the resume\n"
        "- Use format: Replace \"X\" with \"Y\" for change log entries\n\n"

        "7️⃣ Generate a New Optimized Resume:\n"
        "- ATS-compliant formatting\n"
        "- Standard section headers, no tables or graphics\n"
        "- Consistent date formats\n"
        "- Use a clear, professional tone\n"
        "- Do not introduce untrue information\n\n"

        "8️⃣ Return the Output As:\n"
        "- ✅ Compatibility Score (original and optimized)\n"
        "- ✅ Summary of matched and missing skills\n"
        "- ✅ Change Log (\"was\" → \"new\") in JSON format\n"
        "- ✅ Resume improvement rationale\n"
        "- ✅ Final optimized resume text\n\n"

        "9️⃣ Suggest Improvements Breakdown:\n"
        "- List missing and underused keywords\n"
        "- Suggest sentence rewrites per section\n"
        "- Highlight formatting and structural ATS issues\n"
        "- Provide summary and rationale\n\n"
    )

    if prompt_instructions:
        base_prompt += f"\n\n{prompt_instructions}"

    full_prompt = (
        f"{base_prompt}\n\n"
        f"Job Description:\n{jd_text}\n\n"
        f"Resume:\n{resume_text}\n"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Change to gpt-3.5-turbo if needed
            messages=[
                {"role": "system", "content": "You are a professional ATS resume assistant."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.5,
            max_tokens=2000
        )
        return response["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Error contacting OpenAI: {str(e)}"
    
# === Add Cover Letter ===

def generate_cover_letter(resume_text, jd_text, api_key):
    import openai
    openai.api_key = api_key

    prompt = (
        "Act as a professional career assistant. Using the resume and job description provided, "
        "generate a personalized cover letter tailored to the job, leveraging the candidate's experiences, skills, and achievements.\n\n"
        "Requirements:\n"
        "- Align tone and structure with professional cover letter norms.\n"
        "- Do not fabricate experiences.\n"
        "- Include the company name and job title in the letter.\n\n"
        f"Job Description:\n{jd_text}\n\nResume:\n{resume_text}"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a career assistant generating compelling cover letters."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error generating cover letter: {str(e)}"