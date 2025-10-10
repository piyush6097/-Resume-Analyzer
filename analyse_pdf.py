import os
from dotenv import load_dotenv
import google.generativeai as genai

# ✅ Load once globally (not in every function call)
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("Error: GOOGLE_API_KEY not found in environment variables.")

genai.configure(api_key=api_key)

# ✅ Create model once, reuse
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config={
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 4096,
        "response_mime_type": "text/plain"
    }
)

def analyse_resume_gemini(resume_content, job_description):
    prompt = f"""
    You are a professional resume analyzer.

    Resume:
    {resume_content}

    Job Description:
    {job_description}

    Task:
    - Analyze the resume against the job description.
    - Give a match score out of 100.
    - Highlight missing skills or experiences.
    - Suggest improvements.

    Return the result in structured format:
    Match Score: XX/100
    Missing Skills:
    - ...
    Suggestions:
    - ...
    Summary:
    ...
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error from Gemini API: {e}"
