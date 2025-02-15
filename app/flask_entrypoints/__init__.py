import flask, os
from dotenv import load_dotenv


load_dotenv()

adv = flask.Flask('adv')
adv.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")