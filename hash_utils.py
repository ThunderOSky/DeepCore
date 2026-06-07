import hashlib

SALT = "DeepCore_Super_Secret_Salt_2026"

def hash_password(password):
    if not password:
        return ""
    return hashlib.sha256(f"{password}{SALT}".encode()).hexdigest()

def verify_password(password, hashed_password):
    if not password or not hashed_password:
        return False
    return hash_password(password) == hashed_password