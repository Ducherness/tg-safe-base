# lib/crypto.py
import os
import base64
import json
from pathlib import Path

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

CFG_PATH = Path(__file__).parent.parent / 'data' / 'config.json'
CFG_PATH.parent.mkdir(exist_ok=True)
if not CFG_PATH.exists():
    CFG_PATH.write_text(json.dumps({'salt': base64.urlsafe_b64encode(os.urandom(16)).decode()}))

_config = json.loads(CFG_PATH.read_text())

def derive_key(password: str) -> bytes:
    salt = base64.urlsafe_b64decode(_config['salt'].encode())
    password_bytes = password.encode()
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000, backend=default_backend())
    key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
    return key

def encrypt_with_key(key: bytes, plaintext: str) -> str:
    f = Fernet(key)
    token = f.encrypt(plaintext.encode())
    return base64.b64encode(token).decode()

def decrypt_with_key(key: bytes, token_b64: str) -> str:
    f = Fernet(key)
    token = base64.b64decode(token_b64)
    return f.decrypt(token).decode()
