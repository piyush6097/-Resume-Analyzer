# analyse_pdf.py
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

# ✅ Load model once (recommended small & fast model)
model = SentenceTransformer("all-MiniLM-L6-v2")

def clean_text(text):
    """Simple text cleaning."""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def analyse_resume_st(resume_content, job_description):
    """
    Compare resume and JD using SentenceTransformer embeddings.
    Returns a structured result dict.
    """
    resume_text = clean_text(resume_content)
    jd_text = clean_text(job_description)

    # Generate embeddings
    embeddings = model.encode([resume_text, jd_text])
    resume_vec, jd_vec = embeddings[0], embeddings[1]

    # Cosine similarity → scale to 0–100
    similarity = cosine_similarity([resume_vec], [jd_vec])[0][0]
    score = round(float(similarity) * 100, 2)

    # Simple keyword difference for missing skills (optional enhancement)
    resume_words = set(resume_text.lower().split())
    jd_words = set(jd_text.lower().split())
    missing = [w for w in jd_words if w not in resume_words][:10]  # top 10 missing

    result = {
        "score": score,
        "raw_text": f"""
Match Score: {score}/100
Missing Skills / Keywords (sample):
- {', '.join(missing) if missing else 'None'}

Suggestions:
- Include more of the missing skills or keywords in your resume.
- Align experience with the job description for a stronger match.

Summary:
This score measures textual similarity between resume and JD.
"""
    }

    return result
