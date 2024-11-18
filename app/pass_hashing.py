from flask_bcrypt import Bcrypt

from app import adv

bcrypt = Bcrypt(adv)


def hash_password(password: str) -> str:
    password = password.encode()
    return bcrypt.generate_password_hash(password).decode()


def check_password(hashed_password: str, password: str) -> bool:
    hashed_password = hashed_password.encode()
    password = password.encode()
    return bcrypt.check_password_hash(pw_hash=hashed_password, password=password)
