"""Run from the project folder:  python -m unittest discover tests -v
Uses only synthetic images made in code (no real people's pictures)."""
import io, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image, ImageDraw
import app as kavach


def make_image(seed=1, size=(400, 300), fmt="PNG", quality=None):
    img = Image.new("RGB", size, (30 + seed * 40 % 200, 80, 140))
    d = ImageDraw.Draw(img)
    for k in range(6):
        x = (seed * 53 + k * 61) % size[0]
        y = (seed * 29 + k * 47) % size[1]
        d.ellipse([x, y, x + 90, y + 70], fill=((seed * 70 + k * 40) % 255, (k * 60) % 255, 200 - k * 20))
    buf = io.BytesIO()
    kw = {"quality": quality} if quality else {}
    img.save(buf, fmt, **kw)
    buf.seek(0)
    return buf


def resized(buf):
    img = Image.open(buf)
    out = io.BytesIO()
    img.resize((200, 150)).save(out, "PNG")
    out.seek(0)
    return out


class T(unittest.TestCase):
    def setUp(self):
        self.c = kavach.app.test_client()

    def post(self, a, b, an="a.png", bn="b.png"):
        return self.c.post("/compare", data={"image1": (a, an), "image2": (b, bn)},
                           content_type="multipart/form-data")

    def uploads_empty(self):
        return [f for f in os.listdir(kavach.UPLOAD_DIR) if not f.startswith(".")] == []

    def test_identical_files(self):
        r = self.post(make_image(1), make_image(1))
        t = r.get_data(as_text=True)
        self.assertIn("files are byte-for-byte identical", t)
        self.assertIn("Likely the same source image", t)
        self.assertTrue(self.uploads_empty())

    def test_different_images(self):
        t = self.post(make_image(1), make_image(5)).get_data(as_text=True)
        self.assertNotIn("files are byte-for-byte identical", t)

    def test_resized_copy_has_different_sha_but_similar_look(self):
        t = self.post(make_image(2), resized(make_image(2))).get_data(as_text=True)
        self.assertNotIn("files are byte-for-byte identical", t)
        self.assertIn("Likely the same source image", t)

    def test_unsupported_type(self):
        r = self.post(io.BytesIO(b"hello"), make_image(1), "x.exe", "b.png")
        self.assertIn("Only JPG, PNG or WEBP", r.get_data(as_text=True))
        self.assertTrue(self.uploads_empty())

    def test_corrupt_image_cleans_up(self):
        r = self.post(io.BytesIO(b"not an image"), make_image(1), "x.png", "b.png")
        self.assertIn("could not be read", r.get_data(as_text=True))
        self.assertTrue(self.uploads_empty())

    def test_missing_file(self):
        r = self.c.post("/compare", data={}, content_type="multipart/form-data")
        self.assertIn("Please choose both images", r.get_data(as_text=True))

    def test_oversized_upload(self):
        old = kavach.app.config["MAX_CONTENT_LENGTH"]
        kavach.app.config["MAX_CONTENT_LENGTH"] = 1000
        try:
            r = self.post(make_image(1), make_image(2))
            self.assertEqual(r.status_code, 413)
        finally:
            kavach.app.config["MAX_CONTENT_LENGTH"] = old

    def test_verify_match_and_mismatch(self):
        data = make_image(3).getvalue()
        h, _ = kavach.sha256_of_stream(io.BytesIO(data))
        ok = self.c.post("/verify/check", data={"file": (io.BytesIO(data), "a.png"), "expected": h},
                         content_type="multipart/form-data").get_data(as_text=True)
        self.assertIn("Match.", ok)
        bad = self.c.post("/verify/check", data={"file": (io.BytesIO(data + b"x"), "a.png"), "expected": h},
                          content_type="multipart/form-data").get_data(as_text=True)
        self.assertIn("No match.", bad)
        self.assertTrue(self.uploads_empty())

    def test_verify_bad_inputs(self):
        r = self.c.post("/verify/check", data={"file": (io.BytesIO(b"x"), "a.png"), "expected": "abc"},
                        content_type="multipart/form-data")
        self.assertEqual(r.status_code, 400)
        h = "a" * 64
        r = self.c.post("/verify/check", data={"file": (io.BytesIO(b"x"), "a.exe"), "expected": h},
                        content_type="multipart/form-data")
        self.assertEqual(r.status_code, 400)

    def form(self, **extra):
        d = {"verdict": "Appears unrelated", "similarity_percent": "40", "phash_distance": "20",
             "dhash_distance": "18", "average_distance": "19"}
        d.update(extra)
        return d

    def test_report_empty_and_full(self):
        r = self.c.post("/report", data=self.form())
        self.assertEqual(r.mimetype, "application/pdf")
        full = self.form(platform="Insta <b>", source_url="https://example.com/p", noticed_date="2026-10-01",
                         notes="line1\nline2", reference="Case 1", sha256_a="a" * 64, sha256_b="B" * 64,
                         name_a="one.png", name_b="two.png")
        full["actions"] = ["saved_evidence", "bogus"]
        r = self.c.post("/report", data=full)
        self.assertEqual(r.mimetype, "application/pdf")
        self.assertTrue(r.data.startswith(b"%PDF"))

    def test_report_rejects_bad_input(self):
        for bad in ({"source_url": "javascript:alert(1)"}, {"noticed_date": "2999-01-01"},
                    {"noticed_date": "nope"}, {"sha256_a": "xyz"}, {"verdict": "Made up"},
                    {"similarity_percent": "500"}):
            self.assertEqual(self.c.post("/report", data=self.form(**bad)).status_code, 400, bad)

    def test_pages_load(self):
        for p in ("/", "/verify", "/help"):
            self.assertEqual(self.c.get(p).status_code, 200, p)
        self.assertIn("cybercrime.gov.in", self.c.get("/help").get_data(as_text=True))

    def test_xss_escaped(self):
        t = self.post(make_image(1), make_image(1), "<script>x</script>.png", "b.png").get_data(as_text=True)
        self.assertNotIn("<script>x", t)


if __name__ == "__main__":
    unittest.main()
