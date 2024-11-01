from flask_bcrypt import Bcrypt

from app import adv

bcrypt = Bcrypt(adv)


def hash_password(password: str) -> str:
    password = password.encode()
    return bcrypt.generate_password_hash(password).decode()


def check_password(password: str, hashed_password: str) -> bool:
    password = password.encode()
    hashed_password = hashed_password.encode()
    return bcrypt.check_password_hash(password, hashed_password)
