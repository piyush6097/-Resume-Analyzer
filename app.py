from flask import Flask, request, render_template
import os
import fitz  # PyMuPDF

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def extract_text_from_resume(pdf_path):
    """Extract text from uploaded resume PDF."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
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

            try:
                # ✅ Import here (lazy load heavy dependency)
                from analyse_pdf import analyse_resume_gemini
                result = analyse_resume_gemini(resume_content, job_description)
            except Exception as e:
                result = f"Error analyzing resume: {e}"

    return render_template("index.html", result=result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render uses dynamic ports
    app.run(host="0.0.0.0", port=port)
