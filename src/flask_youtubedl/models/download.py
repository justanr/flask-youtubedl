from ..extensions import db
from .base import BaseModel
from .video import Video


class Download(BaseModel, db.Model):
    __tablename__ = "downloads"

    # uuid -- store as string for prototyping
    download_id: str = db.Column(db.Text)
    # could be None!
    # filename that ytdl writes to -- may be different than final filename
    tmpfilename: str = db.Column(db.Text, nullable=True)
    # final filename
    filename: str = db.Column(db.Text, nullable=True)

    # enum? Pending, Downloading, Finished, Failed?
    status: str = db.Column(db.Text, default="Pending")
    # json blob, just store as str for now, it won't be queried
    options: str = db.Column(db.Text, default="{}")

    # video can have multiple downloads
    video_id: int = db.Column(db.Integer, db.ForeignKey("videos.id"))
    video: Video = db.relationship(Video, backref=db.backref("downloads", lazy=True))


class DownloadAttempt(BaseModel, db.Model):
    __tablename__ = "download_attempts"
    total_bytes: int = db.Column(db.Integer, nullable=True)
    downloaded_bytes: int = db.Column(db.Integer, nullable=True)
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
    download_id: int = db.Column(db.Integer, db.ForeignKey("downloads.id"))
    download: Download = db.relationship(
        Download, backref=db.backref("attempts", lazy=True)
    )
