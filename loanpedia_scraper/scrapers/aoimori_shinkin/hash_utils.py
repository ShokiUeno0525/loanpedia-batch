"""Hash utilities (skeleton)."""
import hashlib

def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

