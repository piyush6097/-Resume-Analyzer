# analyse_pdf.py
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

MODEL_NAME = "all-MiniLM-L6-v2"
MODEL_VERSION = "st-all-MiniLM-L6-v1"  # bump this string when you change model or major prompt changes

# load model once
model = SentenceTransformer(MODEL_NAME)

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text or "")
    return text.strip()

def extract_keywords(text: str, top_k: int = 20):
    # Very simple keyword extractor: split words and pick frequent tokens excluding stop-like tokens.
    words = [w.lower().strip(".,()[]{}:;\"'") for w in text.split()]
    # remove very short tokens
    words = [w for w in words if len(w) > 2]
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    # sort by freq
    items = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in items[:top_k]]

def analyse_resume_st(resume_content: str, job_description: str):
    resume_text = clean_text(resume_content)
    jd_text = clean_text(job_description)

    # embed both texts
    embeddings = model.encode([resume_text, jd_text])
    resume_vec, jd_vec = embeddings[0], embeddings[1]

    sim = cosine_similarity([resume_vec], [jd_vec])[0][0]
    score = round(float(sim) * 100, 2)

    # missing keywords (naive)
    resume_kw = set(extract_keywords(resume_text, top_k=200))
    jd_kw = set(extract_keywords(jd_text, top_k=200))
    missing = [w for w in jd_kw if w not in resume_kw][:20]

    raw_text = f"""Match Score: {score}/100
Missing Skills / Keywords (sample):
- {', '.join(missing) if missing else 'None'}

Suggestions:
- Add the top missing keywords/skills and align experience bullets to the JD.
- Consider using role/keyword focused phrases (e.g., "X years of Y", "project: Z").

Summary:
This score is semantic similarity (cosine) between resume and JD embeddings using {MODEL_NAME}.
"""

    return {"raw_text": raw_text, "score": score, "model_version": MODEL_VERSION}
