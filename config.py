import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
        "sqlite:///{0}".format(os.path.join(basedir, "instance", "planner.db"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
