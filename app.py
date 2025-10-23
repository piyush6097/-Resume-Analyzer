# app.py
from flask import Flask, request, render_template, jsonify, redirect, url_for
import os
import fitz  # PyMuPDF
from analyse_pdf import analyse_resume_st
from hash_resume import compute_sha256
from db_cache import init_db, get_cached_score, save_score, add_job_description, list_job_descriptions, list_cached_candidates, delete_cached, get_job_description

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# init db once
init_db()

@app.route("/health")
def health():
    return "OK", 200

def extract_text_from_resume(pdf_path):
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
    jds = list_job_descriptions()

    if request.method == "POST":
        print("\n[INFO] POST request received ✅")

        resume_file = request.files.get("resume")
        job_description = request.form.get("job_description", "")

        print("[DEBUG] Uploaded file:", resume_file)
        print("[DEBUG] Job description length:", len(job_description))

        if not resume_file:
            result = {"raw_text": "No file uploaded."}
        elif not resume_file.filename.endswith(".pdf"):
            result = {"raw_text": "Please upload a valid PDF file."}
        else:
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_file.filename)
            resume_file.save(pdf_path)
            print("[INFO] Resume saved at:", pdf_path)

            # --- Compute hash
            from hash_resume import compute_sha256
            resume_hash = compute_sha256(pdf_path)
            print("[DEBUG] Resume hash:", resume_hash)

            # --- Extract text
            resume_content = extract_text_from_resume(pdf_path)
            print("[INFO] Extracted resume length:", len(resume_content))

            # --- Call model
            from analyse_pdf import analyse_resume_st
            print("[INFO] Running sentence transformer model...")
            result = analyse_resume_st(resume_content, job_description)

            print("[DEBUG RESULT =>]", result)

    return render_template("index.html", result=result, jds=jds)

# --- JD management endpoints (simple) ---
@app.route("/admin/jd/add", methods=["POST"])
def admin_add_jd():
    name = request.form.get("name")
    desc = request.form.get("description", "")
    if not name:
        return "name required", 400
    jd_id = add_job_description(name, desc)
    return redirect(url_for("index"))

@app.route("/admin/jd/list", methods=["GET"])
def admin_list_jd():
    jds = list_job_descriptions()
    return jsonify(jds)

# --- Admin: list cached candidates ---
@app.route("/admin/candidates", methods=["GET"])
def admin_list_candidates():
    rows = list_cached_candidates()
    return jsonify(rows)

# --- Admin: force delete a cached hash (so next upload will re-score) ---
@app.route("/admin/candidate/delete", methods=["POST"])
def admin_delete_candidate():
    resume_hash = request.form.get("resume_hash")
    if not resume_hash:
        return "resume_hash required", 400
    delete_cached(resume_hash)
    return "deleted", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
