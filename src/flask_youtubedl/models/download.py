from ..extensions import db
from .base import BaseModel
from .video import Video


class Download(BaseModel, db.Model):
    __tablename__ = "downloads"

    # uuid -- store as string for prototyping
    download_id: str = db.Column(db.Text)
    # json blob, just store as str for now, it won't be queried
    options: str = db.Column(db.Text, default="{}")
    block_further: bool = db.Column(db.Boolean, default=False)
    block_reason: str = db.Column(db.Text, nullable=True)

    # video can have multiple downloads
    video_id: int = db.Column(db.Integer, db.ForeignKey("videos.id"))
    video: Video = db.relationship(Video, backref=db.backref("downloads", lazy=True))


class DownloadAttempt(BaseModel, db.Model):
    __tablename__ = "download_attempts"
    tmpfilename: str = db.Column(db.Text, nullable=True)
    filename: str = db.Column(db.Text, nullable=True)
    total_bytes: int = db.Column(db.BigInteger, nullable=True)
    downloaded_bytes: int = db.Column(db.BigInteger, nullable=True)
    # seconds, best guess, can be none
    eta: int = db.Column(db.Integer, nullable=True)
    # seconds since download started, none if it hasn't started
    elapsed: float = db.Column(db.Float, nullable=True)
    # bytes/second, can be None
    speed: float = db.Column(db.Float, nullable=True)
    status: str = db.Column(db.Text, default="Pending")
    # how to handle these if/when they occur?
    # fragment_index
    # fragment_count
    error: str = db.Column(db.Text, nullable=True)
    download_id: int = db.Column(db.Integer, db.ForeignKey("downloads.id"))
    download: Download = db.relationship(
        Download, backref=db.backref("attempts", lazy=True)
    )


