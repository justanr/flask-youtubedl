from datetime import datetime
from typing import Optional
from uuid import uuid4

from flask import abort
from flask.views import MethodView
from injector import inject
from sqlalchemy.orm import Session
from youtube_dl import YoutubeDL

from ...core.schema import (
    DownloadAttemptSchema,
    DownloadSchema,
    YtdlDownloadOptionsSchema,
)
from ...core.utils import store_video
from ...core.ytdl_options import YtdlDownloadOptions
from ...extensions import celery
from ...models import Download, DownloadAttempt, Video
from ...models.serialize_result import SerializeResult
from ...worker.tasks import cleanup_attempt, process_video_download
from ..helpers import FytdlBlueprint, read_from_body, serialize_with

__all__ = ("DownloadView", "download")

download = FytdlBlueprint("download", __name__, url_prefix="/download")


class DownloadView(MethodView):
    @inject
    def __init__(self, ytdl: YoutubeDL, session: Session):
        self._ytdl = ytdl
        self._session = session
        self._options_schmea = YtdlDownloadOptionsSchema()

    @serialize_with(schema=DownloadSchema)
    @read_from_body(input_arg_name="options", schema=YtdlDownloadOptionsSchema)
    def post(self, video_id: str, options: SerializeResult[YtdlDownloadOptions] = None):
        dl = self._get_download_from_video_id(video_id)

        if dl and dl.block_further:
            abort(403)

        if dl is None:
            if options is None:
                options = SerializeResult.from_data(YtdlDownloadOptions())

            if options.errors:
                abort(400)

            info = self._ytdl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}", download=False
            )
            video = store_video(info)
            dl = Download()
            dl.download_id = str(uuid4())
            dl.video = video
            self._session.add(dl)

        if (
            not dl.latest_attempt
            or dl.latest_attempt.is_failed()
            or dl.latest_attempt.is_canceled()
        ):
            attempt = dl.start_new_attempt()
            attempt.set_options(self._options_schmea.dump(options.data).data)
            self._session.add(attempt)
            self._session.commit()
            process_video_download.delay(str(dl.download_id))

        return dl

    @serialize_with(schema=DownloadSchema)
    def get(self, video_id: str):
        dl = self._get_download_from_video_id(video_id)
        if not dl:
            abort(404)
        return dl

    def delete(self, video_id: str) -> None:
        dl = self._get_download_from_video_id(video_id)
        if not dl:
            return "", 204

        attempt = dl.latest_attempt

        if (
            not attempt
            or attempt.is_failed()
            or attempt.is_canceled()
            or attempt.is_finished()
        ):
            return "", 204

        attempt.set_canceled(datetime.utcnow())
        self._session.commit()

        async_result = celery.AsyncResult(attempt.task_id)
        if attempt.is_pending():
            async_result.revoke()

        elif attempt.is_downloading():
            async_result.revoke(terminate=True, signal="SIGUSR1")

        cleanup_attempt.delay(attempt.id)
        return "", 204

    def _get_download_from_video_id(self, video_id) -> Optional[Download]:
        return (
            Download.query.join(Video, Download.video)
            .join(DownloadAttempt, Download.attempts)
            .filter(Video.video_id == video_id)
            .first()
        )


class LatestDownloadAttempt(MethodView):
    @serialize_with(schema=DownloadAttemptSchema)
    def get(self, video_id: str):
        dl = (
            Download.query.join(Video, Download.video)
            .join(DownloadAttempt, Download.attempts)
            .filter(Video.video_id == video_id)
            .first()
        )

        if not dl or not (attempt := dl.latest_attempt):
            abort(404)

        return attempt


download.add_url_rule("/video/<video_id>", view_func=DownloadView.as_view("download"))
download.add_url_rule(
    "/video/<video_id>/latest",
    view_func=LatestDownloadAttempt.as_view("latest_attempt"),
)
