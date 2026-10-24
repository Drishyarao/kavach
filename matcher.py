import sys
from PIL import Image, UnidentifiedImageError
import imagehash

MAX_BITS = 64  # each fingerprint is 64 bits long


def fingerprint(path):
    """Open an image and return two 'sketch' fingerprints of how it looks."""
    try:
        with Image.open(path) as img:
            img = img.convert("RGB")
            return imagehash.phash(img), imagehash.dhash(img)
    except (FileNotFoundError, UnidentifiedImageError, OSError) as e:
        raise ValueError(f"Could not read image: {path}") from e


def compare(path_a, path_b):
    """Compare two images and return an honest, cautious verdict."""
    phash_a, dhash_a = fingerprint(path_a)
    phash_b, dhash_b = fingerprint(path_b)

    # Distance = how many bits differ. 0 means identical sketches.
    phash_distance = phash_a - phash_b
    dhash_distance = dhash_a - dhash_b
    avg_distance = (phash_distance + dhash_distance) / 2

    similarity = round((1 - avg_distance / MAX_BITS) * 100, 1)

    if avg_distance <= 10:
        verdict = "Likely the same source image"
    elif avg_distance <= 20:
        verdict = "Possibly related - review manually"
    else:
        verdict = "Appears unrelated"

    return {
        "phash_distance": phash_distance,
        "dhash_distance": dhash_distance,
        "average_distance": avg_distance,
        "similarity_percent": similarity,
        "verdict": verdict,
        "note": "Visual similarity is not proof of copying, "
                "and cannot show whether an image is a deepfake.",
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python matcher.py image1 image2")
        sys.exit(1)
    try:
        result = compare(sys.argv[1], sys.argv[2])
    except ValueError as err:
        print(err)
        sys.exit(1)
    for key, value in result.items():
        print(f"{key}: {value}")