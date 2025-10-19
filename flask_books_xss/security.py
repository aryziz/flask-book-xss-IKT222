from argon2 import PasswordHasher

ph = PasswordHasher(
    memory_cost=19456,  # Memory cost in kibibytes (19 MiB)
    parallelism=1,      # Number of parallel threads
    time_cost=2         # Iteration count
)

def hash_password(pw: str) -> str:
    return ph.hash(pw)

def verify_password(hash_: str, pw: str) -> bool:
    try:
        return ph.verify(hash_, pw)
    except:
        return False