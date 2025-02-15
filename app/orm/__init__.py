from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

POSTGRES_DSN = f"postgresql://adv:secret@127.0.0.1:5431/adv"
engine = create_engine(POSTGRES_DSN)
session_maker = sessionmaker(bind=engine)
