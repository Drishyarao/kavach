# Kavach

**Privacy-first image misuse support tool**
Built for recHERsion 2026 (ACM-W NITK), Problem Statement 2: Women's Safety.
Team: Kavach

Kavach helps someone who finds a suspicious copy of her image online. It compares two images, records a SHA-256 fingerprint of each file, explains the result honestly, and shows where to get help. It runs on your own computer.

## What it does

- **Compare two images** using two perceptual hashes (pHash and dHash) from the ImageHash library. It shows a similarity score and a cautious verdict.
- **File fingerprints (SHA-256)** for both images, so you can later show whether a file is byte-for-byte unchanged.
- **Verify a file**: choose a file, paste a recorded fingerprint, and see Match or No match. The file is checked in memory and not saved.
- **Incident summary PDF**: your own reference, platform, link, date, notes, steps you have taken, the measurements, the file fingerprints and the help list. Images are not put in the PDF.
- **Get help page (India)**: emergency (112, 181), cybercrime reporting (cybercrime.gov.in, 1930), image removal (StopNCII.org, Take It Down) and reporting to the platform.

## How it works

- A resized copy of a photo looks the same, so pHash and dHash say it is likely the same image, but its SHA-256 fingerprint is different because the file changed.
- Similarity score = (1 - average distance / 64) x 100. Verdict bands (average distance 10 or less, 20 or less, otherwise unrelated) are our starting values and have not been validated.

## Setup

Requires Python 3.

```
git clone https://github.com/Drishyarao/kavach.git
cd kavach
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

On macOS or Linux, use `source venv/bin/activate` instead of `venv\Scripts\activate`.

Then open http://127.0.0.1:5000 in your browser.

## Run the tests

```
python -m unittest discover tests -v
```

There are 13 tests. They use synthetic images made in code.

To see how the comparison reacts to edits (resize, JPEG quality, blur, brightness, crops, mirroring) on a synthetic picture, run:

```
python robustness_test.py
```

## Privacy and safety

- Everything runs on your own computer. Nothing is sent to an outside service.
- Uploads are saved under random names, only while comparing, and deleted afterwards. Verify never saves the file.
- Only JPG, PNG and WEBP files can be compared, with a 16 MB limit. Report fields are checked before the PDF is made.
- Test with your own or synthetic images only.

## Limitations

- Visual similarity is not proof of copying or misuse, and the score is not a probability.
- Heavy crops and mirrored copies can make the same image read as unrelated.
- SHA-256 shows a file is unchanged. It does not show who made it, when, or whether it was misused.
- Kavach does not detect deepfakes, search the internet for images, identify who posted an image, contact anyone, or remove content.
- The PDF is a personal summary, not legal evidence.
- Help numbers and websites can change. Check each one before relying on it.

## Future scope

Better handling of heavy crops and edits, a saved and tamper-evident evidence log, and hosting after a full privacy review.

## Credits

- Flask, Pillow, ImageHash, ReportLab (open-source libraries)
- Help information from the india.gov.in directory, StopNCII.org and takeitdown.ncmec.org
- Sample test photos from Pexels
- Built by Drishyarao and harshasalian27-coder, with AI assistance (Claude). We can explain every part of the project.
