from marshmallow import fields as ma_fields
from datetime import datetime
from typing import List

from flask import Flask, jsonify
from flask.views import MethodView
from flask_sqlalchemy import SQLAlchemy
from marshmallow_annotations import AnnotationSchema
from youtube_dl import YoutubeDL

ytdl = YoutubeDL()
ytdl.add_default_info_extractors()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ytdl.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


video_to_playlist = db.Table(
    "video_to_playlist",
    db.Column("video_id", db.Integer, db.ForeignKey("videos.id"), primary_key=True),
    db.Column(
        "playlist_id", db.Integer, db.ForeignKey("playlists.id"), primary_key=True
    ),
)


class Video(db.Model):
    __tablename__ = "videos"

    # preamble
    id: int = db.Column(db.Integer, primary_key=True)
    created: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified: datetime = db.Column(db.DateTime, default=datetime.utcnow)

    # actual shit we care about
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


class Playlist(db.Model):
    __tablename__ = "playlists"

    # preamble
    id: int = db.Column(db.Integer, primary_key=True)
    created: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified: datetime = db.Column(db.DateTime, default=datetime.utcnow)

    # actual shit we care about
    name: str = db.Column(db.String)
    extractor: str = db.Column(db.String)
    playlist_id: str = db.Column(db.String)
    webpage_url: str = db.Column(db.String)


class PlaylistSchema(AnnotationSchema):
    videos = ma_fields.List(ma_fields.Nested("VideoSchema", exclude=("playlists",)))

    class Meta:
        target = Playlist
        register_as_scheme = True


class VideoSchema(AnnotationSchema):
    class Meta:
        target = Video
        register_as_scheme = True

        class Fields:
            playlists = {"exclude": ("videos",)}


def store_video(video_blob, add_to_playlist=None):
    video = Video.query.filter(Video.video_id == video_blob["id"]).first()
    if video is None:
        video = Video()
        video.name = video_blob["title"]
        video.video_id = video_blob["id"]
        video.webpage_url = video_blob["webpage_url"]
        video.duration = video_blob["duration"]
        video.extractor = video_blob["extractor"]

    if add_to_playlist:
        video.playlists.append(add_to_playlist)

    return video


def store_playlist(playlist_blob):
    playlist = Playlist.query.filter(
        Playlist.playlist_id == playlist_blob["id"]
    ).first()
    if playlist is None:
        playlist = Playlist()
        playlist.name = playlist_blob["title"]
        playlist.playlist_id = playlist_blob["id"]
        playlist.extractor = playlist_blob["extractor"]
        playlist.webpage_url = playlist_blob["webpage_url"]

    return playlist


class Debug(MethodView):
    def get(self):
        from marshmallow_annotations.registry import registry
        from marshmallow.class_registry import _registry as ma_registry
        debug = {}
        debug["annotations_registry"] = {repr(k): repr(v) for k,v in registry._registry.items()}
        debug["marshmallow_registry"] = {str(k): [repr(v_) for v_ in v] for k,v in ma_registry.items()}

        return jsonify(debug)


class PlaylistView(MethodView):
    def __init__(self):
        self._ytdl = ytdl

    def get(self, id: str):
        info = self._ytdl.extract_info(
            f"https://www.youtube.com/playlist?list={id}", download=False
        )
        return jsonify(info)

    def post(self, id: str):
        info = self._ytdl.extract_info(
            f"https://www.youtube.com/playlist?list={id}", download=False
        )
        playlist = store_playlist(info)
        for video in info["entries"]:
            store_video(video, playlist)

        db.session.add(playlist)
        db.session.commit()
        return jsonify(PlaylistSchema().dump(playlist).data)


class VideoView(MethodView):
    def __init__(self):
        self._ytdl = ytdl

    def get(self, id: str):
        info = ytdl.extract_info(
            f"https://www.youtube.com/watch?v={id}", download=False
        )
        return jsonify(info)

    def post(self, id: str):
        info = ytdl.extract_info(
            f"https://www.youtube.com/watch?v={id}", download=False
        )
        video = store_video(info)
        db.session.add(video)
        db.session.commit()
        return jsonify(VideoSchema().dump(video).data)


app.add_url_rule("/info/playlist/<id>", view_func=PlaylistView.as_view("playlist-info"))
app.add_url_rule("/info/video/<id>", view_func=VideoView.as_view("video-info"))
app.add_url_rule("/debug", view_func=Debug.as_view("debuggery"))

if __name__ == "__main__":
    db.create_all()
    app.run(use_reloader=True, debug=True)
