# app.py
from flask import Flask, request, render_template
import os
import fitz  # PyMuPDF
from analyse_pdf import analyse_resume_gemini
from hash_resume import compute_sha256
from db_cache import init_db, get_cached_score, save_score

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ✅ create DB table once at startup
init_db()

@app.route("/health")
def health():
    return "OK", 200


def extract_text_from_resume(pdf_path):
    """Extract text from PDF safely."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"


@app.route("/", methods=["GET", "POST"])
def index():
    result = None

    if request.method == "POST":
        resume_file = request.files.get("resume")
        job_description = request.form.get("job_description", "")

        if not resume_file:
            result = "No file uploaded."
        elif not resume_file.filename.endswith(".pdf"):
            result = "Please upload a valid PDF file."
        else:
            # Save uploaded PDF
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_file.filename)
            resume_file.save(pdf_path)

            # ✅ compute SHA-256 hash
            resume_hash = compute_sha256(pdf_path)

            # ✅ check cache
            cached_score = get_cached_score(resume_hash)
            if cached_score is not None:
                result = f"(CACHED RESULT)\n\nCached Score: {cached_score}/100"
            else:
                # extract text + call Gemini
                resume_content = extract_text_from_resume(pdf_path)
                analysis = analyse_resume_gemini(resume_content, job_description)
                result_text = analysis["raw_text"]
                score = analysis["score"]

                # ✅ save to cache
                save_score(resume_hash, score)
                result = f"{result_text}\n\n(Saved Hash: {resume_hash})"

    return render_template("index.html", result=result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
