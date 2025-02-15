import bcrypt


def hash_password(password: str) -> str:
    password = password.encode()
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password=password, salt=salt).decode()


def check_password(hashed_password: str, password: str) -> bool:
    hashed_password = hashed_password.encode()
    password = password.encode()
    return bcrypt.checkpw(password=password, hashed_password=hashed_password)
