"""Kavach robustness check. Run:  python robustness_test.py
Makes a synthetic test picture (no real person's photo), edits it in several ways,
and prints what Kavach's matcher says. Results depend on the real ImageHash library,
so quote only numbers from YOUR OWN run."""
import io, os, tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from matcher import compare


def base():
    img = Image.new("RGB", (800, 600), (40, 90, 150))
    d = ImageDraw.Draw(img)
    for k in range(14):
        x, y = (k * 97) % 700, (k * 61) % 500
        d.ellipse([x, y, x + 140, y + 100], fill=((k * 53) % 255, (k * 91) % 255, (k * 29 + 80) % 255))
        d.rectangle([x + 20, y + 60, x + 120, y + 130], outline=(255, 255, 255), width=4)
    return img


def jpeg(img, q):
    b = io.BytesIO(); img.save(b, "JPEG", quality=q); b.seek(0)
    return Image.open(b).convert("RGB")


def crop(img, f):
    w, h = img.size; dx, dy = int(w * f / 2), int(h * f / 2)
    return img.crop((dx, dy, w - dx, h - dy))


original = base()
cases = [
    ("Same picture (control)", original),
    ("Resized to 50%", original.resize((400, 300))),
    ("Resized to 25%", original.resize((200, 150))),
    ("JPEG quality 70", jpeg(original, 70)),
    ("JPEG quality 30", jpeg(original, 30)),
    ("Slight blur", original.filter(ImageFilter.GaussianBlur(2))),
    ("Brightness +30%", ImageEnhance.Brightness(original).enhance(1.3)),
    ("Crop 10% off edges", crop(original, 0.10)),
    ("Crop 30% off edges", crop(original, 0.30)),
    ("Mirrored left-right", original.transpose(Image.FLIP_LEFT_RIGHT)),
    ("Different picture (control)", Image.new("RGB", (800, 600), (200, 40, 40))),
]

with tempfile.TemporaryDirectory() as tmp:
    a = os.path.join(tmp, "original.png"); original.save(a)
    print("{:<30}{:>7}{:>7}{:>7}{:>9}  {}".format("Edit", "pHash", "dHash", "avg", "sim %", "verdict"))
    for name, img in cases:
        p = os.path.join(tmp, "x.png"); img.save(p)
        r = compare(a, p)
        print("{:<30}{:>7}{:>7}{:>7}{:>9}  {}".format(name, r["phash_distance"], r["dhash_distance"],
              r["average_distance"], r["similarity_percent"], r["verdict"]))
print("\nThese numbers come from synthetic images. Thresholds are starting values, not validated.")
