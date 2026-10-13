"""DARK2 Ed25519 request signing; callers must send the exact signed bytes."""
import base64
import hashlib
import time
import uuid


def public_key_bytes(value: str) -> bytes:
    value = value.strip()
    if "\n" in value or "\r" in value:
        raise ValueError("Expected a single public key")
    if value.startswith("ssh-ed25519 "):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        public = serialization.load_ssh_public_key(value.encode("ascii"))
        if not isinstance(public, Ed25519PublicKey):
            raise ValueError("Expected an Ed25519 public key")
        key = public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    else:
        key = base64.b64decode(value, validate=True)
    if len(key) != 32 or not any(key):
        raise ValueError("Expected an Ed25519 public key (OpenSSH or raw base64)")
    return key


def key_id(key: bytes) -> str:
    return hashlib.sha256(key).hexdigest()


def canonical_request(method, path, authority, fingerprint, timestamp, nonce, digest):
    fields = ["DARK2", method.upper(), path, authority, fingerprint, timestamp, nonce, digest]
    if any(not isinstance(v, str) or not v or "\n" in v or "\r" in v for v in fields):
        raise ValueError("Invalid canonical request field")
    return "\n".join(fields).encode("utf-8")


def sign_request(private_key, method, path, body: bytes, authority: str):
    from cryptography.hazmat.primitives import serialization
    key = private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    timestamp, nonce = str(int(time.time())), str(uuid.uuid4())
    digest, fingerprint = hashlib.sha256(body).hexdigest(), key_id(key)
    signature = private_key.sign(canonical_request(method, path, authority, fingerprint, timestamp, nonce, digest))
    return {
        "X-DARK-Authority-Id": authority,
        "X-DARK-Key-Id": fingerprint, "X-DARK-Timestamp": timestamp,
        "X-DARK-Nonce": nonce, "X-DARK-Content-SHA256": digest,
        "X-DARK-Signature": base64.b64encode(signature).decode("ascii"),
    }
