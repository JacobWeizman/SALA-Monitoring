# -*- coding: utf-8 -*-
"""Verschluesselt die Dashboard-Daten (AES-256-GCM, Schluessel via PBKDF2-SHA256).
Format passt 1:1 zur WebCrypto-Entschluesselung im Browser (render.dashboard_html)."""
import os, json, base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ITER = 250_000


def encrypt_payload(obj, password):
    salt = os.urandom(16)
    iv = os.urandom(12)
    key = PBKDF2HMAC(algorithm=SHA256(), length=32, salt=salt, iterations=ITER).derive(password.encode("utf-8"))
    ct = AESGCM(key).encrypt(iv, json.dumps(obj, ensure_ascii=False).encode("utf-8"), None)
    b = lambda x: base64.b64encode(x).decode()
    return {"salt": b(salt), "iv": b(iv), "ct": b(ct), "iter": ITER}
