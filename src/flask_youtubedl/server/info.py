from flask import jsonify
from flask.views import MethodView
from injector import inject
from sqlalchemy.orm import Session
from youtube_dl import YoutubeDL

from ..core.schema import PlaylistSchema, VideoSchema
from ..core.utils import store_playlist, store_video
from ..models import Playlist, Video
from ._helpers import FytdlBlueprint
from .serialize import serialize_with

info = FytdlBlueprint("info", __name__, url_prefix="/info")


class PlaylistView(MethodView):
    @inject
    def __init__(self, ytdl: YoutubeDL, session: Session):
        self._ytdl = ytdl
        self._session = session

    def get(self, id: str):
        info = self._ytdl.extract_info(
            f"https://www.youtube.com/playlist?list={id}", download=False
        )
        return jsonify(info)

    @serialize_with(schema=PlaylistSchema)
    def post(self, id: str):
        info = self._ytdl.extract_info(
            f"https://www.youtube.com/playlist?list={id}", download=False
        )
        playlist = store_playlist(info)
        for video in info["entries"]:
            store_video(video, playlist)

        self._session.add(playlist)
        self._session.commit()
        return playlist


class VideoView(MethodView):
    @inject
    def __init__(self, ytdl: YoutubeDL, session: Session):
        self._ytdl = ytdl
        self._session = session

    def get(self, id: str):
        info = self._ytdl.extract_info(
            f"https://www.youtube.com/watch?v={id}", download=False
        )
        return jsonify(info)

    @serialize_with(schema=VideoSchema)
    def post(self, id: str):
        info = self._ytdl.extract_info(
            f"https://www.youtube.com/watch?v={id}", download=False
        )
        video = store_video(info)
        self._session.add(video)
        self._session.commit()
        return video


info.add_url_rule("/video/<id>", view_func=VideoView.as_view("video"))
info.add_url_rule("/playlist/<id>", view_func=PlaylistView.as_view("playlist"))
