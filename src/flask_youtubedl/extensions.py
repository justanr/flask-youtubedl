from celery import Celery
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
celery = Celery("fytdl")
