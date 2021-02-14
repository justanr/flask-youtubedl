from datetime import datetime

from ..extensions import db


class BaseModel:
    id: int = db.Column(db.Integer, primary_key=True)
    created: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified: datetime = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
