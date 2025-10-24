from flask import Flask, request, render_template, jsonify, redirect, url_for
import os
import fitz  # PyMuPDF
from analyse_pdf import analyse_resume_st
from hash_resume import compute_sha256
from db_cache import (
    init_db,
    get_cached_score,
    save_score,
    add_job_description,
    list_job_descriptions,
    list_cached_candidates,
    delete_cached,
    get_job_description
)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database once
init_db()


@app.route("/health")
def health():
    return "OK", 200


def extract_text_from_resume(pdf_path):
    """Extract text from a PDF using PyMuPDF"""
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
    jds = list_job_descriptions()  # Fetch all saved JDs

    if request.method == "POST":
        print("\n[INFO] POST request received ✅")

        resume_file = request.files.get("resume")
        job_description = request.form.get("job_description", "")
        selected_jd_id = request.form.get("jd_id", "")

        if not resume_file:
            result = {"raw_text": "No file uploaded."}
        elif not resume_file.filename.endswith(".pdf"):
            result = {"raw_text": "Please upload a valid PDF file."}
        else:
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_file.filename)
            resume_file.save(pdf_path)
            print("[INFO] Resume saved at:", pdf_path)

            # Compute hash
            resume_hash = compute_sha256(pdf_path)
            print("[DEBUG] Resume hash:", resume_hash)

            # Get JD text (from dropdown or textarea)
            jd_text = ""
            if selected_jd_id:
                jd_row = get_job_description(int(selected_jd_id))
                if jd_row:
                    jd_text = jd_row[2]  # JD description text
                    print(f"[INFO] Selected JD: {jd_row[1]}")
            if job_description.strip():
                jd_text = job_description  # override with pasted JD if provided

            # Check if cached
            from analyse_pdf import MODEL_VERSION as CURRENT_MODEL_VERSION
            cached_score = get_cached_score(resume_hash, CURRENT_MODEL_VERSION)

            if cached_score is not None:
                print("[CACHE HIT] Returning cached score ✅")
                result = {"cached": True, "score": cached_score, "resume_hash": resume_hash}
            else:
                print("[CACHE MISS] Running SentenceTransformer model...")
                resume_content = extract_text_from_resume(pdf_path)
                analysis = analyse_resume_st(resume_content, jd_text)
                score = analysis["score"]
                model_version = analysis.get("model_version", CURRENT_MODEL_VERSION)

                jd_id_int = int(selected_jd_id) if selected_jd_id else None
                save_score(
                    resume_hash,
                    score,
                    model_version=model_version,
                    jd_id=jd_id_int,
                    source_filename=resume_file.filename
                )
                result = {
                    "cached": False,
                    "score": score,
                    "resume_hash": resume_hash,
                    "raw_text": analysis["raw_text"]
                }

    return render_template("index.html", result=result, jds=jds)


# ========== JD MANAGEMENT ROUTES ==========

@app.route("/admin/jd/add", methods=["POST"])
def admin_add_jd():
    """Add or update a Job Description"""
    name = request.form.get("name")
    desc = request.form.get("description", "")
    if not name:
        return "JD name required", 400
    add_job_description(name, desc)
    print(f"[INFO] JD '{name}' added to database ✅")
    return redirect(url_for("index"))


@app.route("/admin/jd/list", methods=["GET"])
def admin_list_jd():
    """List all stored JDs"""
    jds = list_job_descriptions()
    return jsonify(jds)


# ========== CANDIDATE CACHE MANAGEMENT ==========

@app.route("/admin/candidates", methods=["GET"])
def admin_list_candidates():
    rows = list_cached_candidates()
    return jsonify(rows)


@app.route("/admin/candidate/delete", methods=["POST"])
def admin_delete_candidate():
    resume_hash = request.form.get("resume_hash")
    if not resume_hash:
        return "resume_hash required", 400
    delete_cached(resume_hash)
    return "deleted", 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


