import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-aeternalib")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "aeternalib.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOAN_DAYS = 14  # días de préstamo por defecto