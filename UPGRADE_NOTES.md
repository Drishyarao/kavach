# Kavach upgrade notes

## What was added (existing routes `/`, `/compare`, `/report` still work the same)
- **SHA-256 fingerprints** of both files on the result page and in the PDF (`integrity.py`).
- **/verify**: choose a file + paste a recorded fingerprint -> match / no match. File is hashed in memory, never saved.
- **/help (Action centre)**: emergency vs cybercrime reporting vs image removal vs platform reporting (`resources.py`).
- **PDF**: reference, file names + fingerprints, steps ticked, help list, clear split of user-entered vs automatic.
- **tests/** (13 tests) and **robustness_test.py**.

## Honest limits
- SHA-256 only shows a file is byte-for-byte unchanged. It does not prove who made it, when, or misuse.
- Perceptual hashes show visual similarity, not proof, not a probability, not deepfake detection.
- Thresholds (<=10, <=20) are starting values and are not validated.
- Kavach does not search the internet, contact police, or remove content.
- Open every link in resources.py before the demo.

## Credits
Flask, Pillow, ImageHash, ReportLab. Built with AI assistance (Claude); we can explain every part.

## Demo script (about 3 min)
1. Home -> upload an original and a resized copy -> result: low pHash distance, DIFFERENT SHA-256.
2. Say: "Same picture to the eye, different file to a computer. That is why we use both."
3. Upload the same file twice -> "byte-for-byte identical".
4. Fill the form, tick steps, download the PDF -> show fingerprints and help list.
5. /verify -> original + pasted fingerprint = Match; edited file = No match.
6. /help -> point out emergency vs cybercrime vs removal.
7. Close with limitations.
