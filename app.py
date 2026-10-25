import io
import os
import uuid
from datetime import date, datetime
from urllib.parse import urlparse
from xml.sax.saxutils import escape

from flask import Flask, render_template, request, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from integrity import hashes_match, normalise_hash, sha256_of_path, sha256_of_stream
from matcher import compare
from resources import ACTIONS, RESOURCES

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
# Files you may fingerprint on the Verify page (they are hashed, never opened or kept).
VERIFY_EXTENSIONS = ALLOWED_EXTENSIONS | {".gif", ".bmp", ".pdf", ".txt"}
ACTION_KEYS = {key for key, _ in ACTIONS}

KNOWN_VERDICTS = {
    "Likely the same source image",
    "Possibly related - review manually",
    "Appears unrelated",
}


def save_temp(file_storage):
    if file_storage is None or file_storage.filename == "":
        raise ValueError("Please choose both images.")
    ext = os.path.splitext(file_storage.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Only JPG, PNG or WEBP images are allowed.")
    path = os.path.join(UPLOAD_DIR, uuid.uuid4().hex + ext)
    file_storage.save(path)
    return path


def clean_text(value, max_len):
    value = (value or "").strip()[:max_len]
    return "".join(ch for ch in value if ch == "\n" or ch >= " ")


def display_name(filename):
    """A short, safe name to show on screen (never used as a path)."""
    return clean_text(os.path.basename(filename or ""), 80) or "unnamed file"


def parse_number(value, low, high):
    number = float(value)
    if not (low <= number <= high):
        raise ValueError("number out of range")
    return number


def read_report_form(form):
    """Read and check everything the report form sent. Raises ValueError if invalid."""
    verdict = clean_text(form.get("verdict"), 80)
    if verdict not in KNOWN_VERDICTS:
        raise ValueError("bad verdict")

    data = {
        "verdict": verdict,
        "similarity": parse_number(form.get("similarity_percent"), 0, 100),
        "phash": parse_number(form.get("phash_distance"), 0, 64),
        "dhash": parse_number(form.get("dhash_distance"), 0, 64),
        "average": parse_number(form.get("average_distance"), 0, 64),
        "platform": clean_text(form.get("platform"), 80),
        "notes": clean_text(form.get("notes"), 1000),
        "reference": clean_text(form.get("reference"), 80),
        "name_a": clean_text(form.get("name_a"), 80),
        "name_b": clean_text(form.get("name_b"), 80),
    }

    # File fingerprints are optional, but if present they must look like real SHA-256 values.
    for key in ("sha256_a", "sha256_b"):
        raw = clean_text(form.get(key), 80)
        if raw and not normalise_hash(raw):
            raise ValueError("bad fingerprint")
        data[key] = normalise_hash(raw) or ""

    # Actions are tick-boxes; only accept the ones we offered.
    data["actions"] = [a for a in form.getlist("actions") if a in ACTION_KEYS]

    url = clean_text(form.get("source_url"), 500)
    if url:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError("bad url")
    data["url"] = url

    noticed = clean_text(form.get("noticed_date"), 10)
    if noticed:
        parsed_date = datetime.strptime(noticed, "%Y-%m-%d").date()
        if parsed_date > date.today():
            raise ValueError("future date")
    data["date"] = noticed

    return data


def build_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Kavach summary",
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle("KTitle", parent=styles["Title"], textColor=colors.HexColor("#603b87"))
    heading = ParagraphStyle("KHeading", parent=styles["Heading2"], textColor=colors.HexColor("#603b87"))
    body = ParagraphStyle("KBody", parent=styles["BodyText"], leading=15, wordWrap="CJK")
    small = ParagraphStyle("KSmall", parent=body, fontSize=9, textColor=colors.HexColor("#555555"))

    def text(value):
        return escape(value).replace("\n", "<br/>") if value else "Not provided"

    story = [
        Paragraph("Kavach - Incident Summary", title),
        Paragraph("Generated on " + datetime.now().strftime("%d %b %Y, %H:%M"), small),
        Spacer(1, 8),
        Paragraph(
            "This is a personal summary to help you stay organised. It is not legal evidence "
            "and has not been verified by anyone.",
            body,
        ),
        Spacer(1, 6),
        Paragraph("<b>Reference:</b> " + text(data["reference"]), body),
        Paragraph("1. Details entered by the user", heading),
        Paragraph("<b>Platform:</b> " + text(data["platform"]), body),
        Paragraph("<b>Page link:</b> " + text(data["url"]), body),
        Paragraph("<b>Date noticed:</b> " + text(data["date"]), body),
        Paragraph("<b>Notes:</b> " + text(data["notes"]), body),
        Paragraph("<b>Steps taken (ticked by the user):</b> " + text(
            "; ".join(label for key, label in ACTIONS if key in data["actions"]) or ""), body),
        Spacer(1, 6),
        Paragraph("2. Automated comparison measurements", heading),
        Paragraph(
            "These numbers were produced by the Kavach tool from two images during this session. "
            "They were not independently verified, and the images themselves are not included "
            "in this report.",
            small,
        ),
        Spacer(1, 4),
    ]

    table = Table(
        [
            ["Measurement", "Value"],
            ["Tool verdict", data["verdict"]],
            ["Visual similarity score", "{:g}%".format(data["similarity"])],
            ["pHash distance (0 = identical)", "{:g}".format(data["phash"])],
            ["dHash distance (0 = identical)", "{:g}".format(data["dhash"])],
            ["Average distance", "{:g}".format(data["average"])],
        ],
        colWidths=[75 * mm, 90 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#603b87")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9b8dd")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story += [table, Spacer(1, 8)]

    if data["sha256_a"] or data["sha256_b"]:
        cell = ParagraphStyle("KCell", parent=small, fontName="Courier", fontSize=7.5, leading=9, wordWrap="CJK")
        label = ParagraphStyle("KLabel", parent=small, wordWrap="CJK")
        fp = Table(
            [
                [Paragraph("File", label), Paragraph("SHA-256 fingerprint", label)],
                [Paragraph(escape(data["name_a"] or "Image 1"), label), Paragraph(data["sha256_a"] or "-", cell)],
                [Paragraph(escape(data["name_b"] or "Image 2"), label), Paragraph(data["sha256_b"] or "-", cell)],
            ],
            colWidths=[45 * mm, 120 * mm],
        )
        fp.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9b8dd")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#efe6f8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story += [
            Paragraph("File fingerprints (SHA-256)", heading),
            Paragraph(
                "A SHA-256 fingerprint changes if even one byte of the file changes. It can show "
                "whether a file is byte-for-byte the same later. It does not show who made the "
                "file, when it was made, or whether it was misused.",
                small,
            ),
            Spacer(1, 4),
            fp,
            Spacer(1, 10),
        ]

    story += [
        Paragraph("3. Limitations", heading),
        Paragraph(
            "Visual similarity is not proof of copying or misuse, and the score is not a "
            "probability. This tool cannot identify who shared an image, show whether it was "
            "shared without permission, or detect deepfakes. Cropping, resizing, filters and "
            "other edits can change the result in either direction.",
            body,
        ),
        Spacer(1, 6),
        Paragraph("4. Suggested next steps", heading),
        Paragraph(
            "Keep the original files, screenshots, links and dates. Use the platform's own "
            "reporting option. Talk to someone you trust. If you feel unsafe, contact local "
            "emergency services.",
            body,
        ),
        Spacer(1, 6),
        Paragraph("5. Where to get help (India)", heading),
        Paragraph(
            "Kavach does not contact anyone or file anything for you. Check each service "
            "yourself before relying on it.",
            small,
        ),
    ]
    for item in RESOURCES:
        line = "<b>" + escape(item["name"]) + "</b>"
        if item["url"]:
            line += " - " + escape(item["url"])
        story.append(Paragraph(line + "<br/>" + escape(item["what"]), body))
        story.append(Spacer(1, 3))

    doc.build(story)
    buffer.seek(0)
    return buffer


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
            result = dict(compare(saved[0], saved[1]))
        except ValueError:
            raise ValueError("One of the files could not be read as an image.")
        # Extra, additive fields: the existing template variables are untouched.
        result["sha256_a"], result["size_a"] = sha256_of_path(saved[0])
        result["sha256_b"], result["size_b"] = sha256_of_path(saved[1])
        result["same_file"] = hashes_match(result["sha256_a"], result["sha256_b"])
        result["name_a"] = display_name(request.files["image1"].filename)
        result["name_b"] = display_name(request.files["image2"].filename)
        return render_template("result.html", result=result, actions=ACTIONS)
    except ValueError as err:
        return render_template("result.html", error=str(err))
    finally:
        for path in saved:
            try:
                os.remove(path)
            except OSError:
                pass


@app.route("/report", methods=["POST"])
def report():
    try:
        data = read_report_form(request.form)
    except (ValueError, TypeError):
        return render_template(
            "result.html",
            error="The report details were not valid. Please compare your images again and "
            "check the link and date you entered.",
        ), 400
    pdf = build_pdf(data)
    return send_file(
        pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="kavach-summary.pdf",
    )


@app.route("/help")
def help_page():
    return render_template("help.html", resources=RESOURCES)


@app.route("/verify")
def verify_page():
    return render_template("verify.html")


@app.route("/verify/check", methods=["POST"])
def verify_check():
    """Hash an uploaded file in memory and compare it to a fingerprint the user pastes.
    Nothing is saved to disk."""
    expected = normalise_hash(request.form.get("expected"))
    upload = request.files.get("file")
    if not expected:
        return render_template("verify.html", error="That does not look like a SHA-256 fingerprint "
                               "(64 characters, 0-9 and a-f)."), 400
    if upload is None or upload.filename == "":
        return render_template("verify.html", error="Please choose a file to check."), 400
    ext = os.path.splitext(upload.filename)[1].lower()
    if ext not in VERIFY_EXTENSIONS:
        return render_template("verify.html", error="That file type is not supported here."), 400
    actual, size = sha256_of_stream(upload.stream)
    return render_template(
        "verify.html",
        checked=True,
        match=hashes_match(actual, expected),
        actual=actual,
        expected=expected,
        name=display_name(upload.filename),
        size=size,
    )


@app.errorhandler(413)
def too_large(_):
    return render_template(
        "result.html", error="Those files are too large. Please use smaller images."
    ), 413


if __name__ == "__main__":
    app.run(debug=True)