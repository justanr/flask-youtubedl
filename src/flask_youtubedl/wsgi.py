from .app import make_app
from .extensions import db

app = make_app(None, None)

with app.app_context():
    db.create_all()
