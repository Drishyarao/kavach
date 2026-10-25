"""File-integrity helpers for Kavach.

SHA-256 turns any file into a 64-character fingerprint. If even one byte of the file
changes, the fingerprint changes completely. That makes it good for answering one
question only: "is this file byte-for-byte the same as before?"

It does NOT show who made the file, when it was created, or whether anything abusive
happened.
"""
import hashlib
import hmac
import re

CHUNK_SIZE = 1024 * 1024  # read files 1 MB at a time

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def sha256_of_stream(stream):
    """Fingerprint an open file-like object without saving it anywhere."""
    digest = hashlib.sha256()
    total = 0
    while True:
        chunk = stream.read(CHUNK_SIZE)
        if not chunk:
            break
        digest.update(chunk)
        total += len(chunk)
    return digest.hexdigest(), total


def sha256_of_path(path):
    """Fingerprint a file on disk. Returns (hex fingerprint, size in bytes)."""
    with open(path, "rb") as handle:
        return sha256_of_stream(handle)


def normalise_hash(text):
    """Clean up a fingerprint the user pasted. Returns None if it is not a valid one."""
    cleaned = (text or "").strip().lower().replace(" ", "")
    return cleaned if _SHA256_PATTERN.match(cleaned) else None


def hashes_match(first, second):
    """Compare two fingerprints safely."""
    return hmac.compare_digest(first, second)
