from argon2 import PasswordHasher

ph = PasswordHasher()

def hash_password(pw: str) -> str:
    return ph.hash(pw)

def verify_password(hash_: str, pw: str) -> bool:
    try:
        return ph.verify(hash_, pw)
    except:
        return False