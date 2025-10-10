

from flask import Flask, request, render_template
import os
import fitz  # PyMuPDF
from analyse_pdf import analyse_resume_gemini

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route("/health")
def health():
    return "OK", 200


def extract_text_from_resume(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()  # ✅ Close to release memory
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
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_file.filename)
            resume_file.save(pdf_path)
            resume_content = extract_text_from_resume(pdf_path)
            result = analyse_resume_gemini(resume_content, job_description)

    return render_template("index.html", result=result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)



