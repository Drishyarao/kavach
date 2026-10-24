import os
import uuid
from flask import Flask, render_template, request
from matcher import compare

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def save_temp(file_storage):
    if file_storage is None or file_storage.filename == "":
        raise ValueError("Please choose both images.")
    ext = os.path.splitext(file_storage.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Only JPG, PNG or WEBP images are allowed.")
    path = os.path.join(UPLOAD_DIR, uuid.uuid4().hex + ext)
    file_storage.save(path)
    return path

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/compare", methods=["POST"])
def compare_images():
    saved = []
    try:
        saved.append(save_temp(request.files.get("image1")))
        saved.append(save_temp(request.files.get("image2")))
        try:
            result = compare(saved[0], saved[1])
        except ValueError:
            raise ValueError("One of the files could not be read as an image.")
        return render_template("result.html", result=result)
    except ValueError as err:
        return render_template("result.html", error=str(err))
    finally:
        for path in saved:
            try:
                os.remove(path)
            except OSError:
                pass

@app.errorhandler(413)
def too_large(_):
    return render_template("result.html", error="Those files are too large. Please use smaller images."), 413

if __name__ == "__main__":
    app.run(debug=True)