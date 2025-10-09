import os
from dotenv import load_dotenv
import google.generativeai as genai

def analyse_resume_gemini(resume_content, job_description):
    # Load environment variable
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "Error: GOOGLE_API_KEY not found. Please set it in your environment variables."

    # Configure Gemini API
    genai.configure(api_key=api_key)
    configuration = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain"
    }

    # Create model instance inside function (not global)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=configuration
    )

    # Prompt for analysis
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

    # Generate response
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error from Gemini API: {e}"
