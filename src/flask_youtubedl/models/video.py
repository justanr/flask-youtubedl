from typing import List

from ..extensions import db
from .base import BaseModel

video_to_playlist = db.Table(
    "video_to_playlist",
    db.Column("video_id", db.Integer, db.ForeignKey("videos.id"), primary_key=True),
    db.Column(
        "playlist_id", db.Integer, db.ForeignKey("playlists.id"), primary_key=True
    ),
)


class Video(BaseModel, db.Model):
    __tablename__ = "videos"

    name: str = db.Column(db.String)
    video_id: str = db.Column(db.String)
    webpage_url: str = db.Column(db.String)
    duration: int = db.Column(db.Integer)
    status: str = db.Column(db.String)
    extractor: str = db.Column(db.String)

    playlists: List["Playlist"] = db.relationship(
        lambda: Playlist,
        secondary=video_to_playlist,
        lazy="subquery",
        backref=db.backref("videos", lazy=True),
    )


class Playlist(BaseModel, db.Model):
    __tablename__ = "playlists"

    playlist_name: str = db.Column(db.String)
    extractor: str = db.Column(db.String)
    playlist_id: str = db.Column(db.String)
    webpage_url: str = db.Column(db.String)
