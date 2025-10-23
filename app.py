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
        resume_file = request.files.get("resume")
        job_description = request.form.get("job_description", "")
        selected_jd_id = request.form.get("jd_id")  # optional

        if not resume_file:
            result = "No file uploaded."
        elif not resume_file.filename.endswith(".pdf"):
            result = "Please upload a valid PDF file."
        else:
            # save file
            filename = resume_file.filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            resume_file.save(save_path)

            # compute hash
            resume_hash = compute_sha256(save_path)

            # check cache (uses model_version from analyse function)
            # we'll call analyse_resume_st only if not cached
            # get model_version from analyse function result after compute (so we call model once if not cached)
            # But first, check if any cached for same model version exists:
            # We'll get model_version by calling analyse_resume_st with empty data? Instead, proceed:
            # check for any cached score irrespective of model_version (if you want strict check include model_version)
            # Here we check by current model_version:
            # call analyse once only when needed
            # We'll use analyse function to get model_version on first run

            # simple path: check cache for CURRENT model_version
            # to get current model_version, call analyse on empty strings? Instead we call analyse only when needed below.

            from analyse_pdf import MODEL_VERSION as CURRENT_MODEL_VERSION

            cached_score = get_cached_score(resume_hash, model_version=CURRENT_MODEL_VERSION)
            if cached_score is not None:
                result = {"cached": True, "score": cached_score, "resume_hash": resume_hash}
            else:
                resume_text = extract_text_from_resume(save_path)
                # If the user selected a JD id, fetch JD text
                jd_text = ""
                if selected_jd_id:
                    jd_row = get_job_description(int(selected_jd_id))
                    if jd_row:
                        jd_text = jd_row[2]  # description field
                # prefer job_description from form if provided
                if job_description.strip():
                    jd_text = job_description

                analysis = analyse_resume_st(resume_text, jd_text)
                score = analysis["score"]
                model_version = analysis.get("model_version", "v1")
                # save to DB
                save_score(resume_hash, score, model_version=model_version, jd_id=int(selected_jd_id) if selected_jd_id else None, source_filename=filename)
                result = {"cached": False, "score": score, "resume_hash": resume_hash, "raw_text": analysis["raw_text"]}

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
