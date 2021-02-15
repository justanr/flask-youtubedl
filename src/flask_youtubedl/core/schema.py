from marshmallow import fields as ma_fields, post_load
from marshmallow_annotations import AnnotationSchema

from ..models import (
    Download,
    DownloadAttempt,
    Pagination,
    PaginationData,
    Playlist,
    Video,
)
from .ytdl_options import YtdlDownloadOptions


class PlaylistSchema(AnnotationSchema):
    videos = ma_fields.List(ma_fields.Nested("VideoSchema", exclude=("playlists",)))

    class Meta:
        target = Playlist
        register_as_scheme = True


class VideoSchema(AnnotationSchema):
    downloads = ma_fields.List(
        ma_fields.Nested("DownloadSchema", exclude=("video", "video_id"))
    )

    class Meta:
        target = Video
        register_as_scheme = True

        class Fields:
            playlists = {"exclude": ("videos",)}


class DownloadSchema(AnnotationSchema):
    _IGNORED_ATTEMPT_FILEDS = ("download", "download_id", "video", "video_id")

    attempts = ma_fields.List(
        ma_fields.Nested("DownloadAttemptSchema", exclude=_IGNORED_ATTEMPT_FILEDS)
    )
    latest_attempt = ma_fields.Nested(
        "DownloadAttemptSchema", exclude=_IGNORED_ATTEMPT_FILEDS
    )

    class Meta:
        target = Download
        register_as_scheme = True

        class Fields:
            video = {"exclude": ("downloads",)}


class DownloadAttemptSchema(AnnotationSchema):
    class Meta:
        target = DownloadAttempt
        register_as_scheme = True

        class Fields:
            download = {"exclude": ("attempts", "latest_attempt", "video", "video_id")}
            video = {"exclude": ("downloads",)}


class PaginationDataSchema(AnnotationSchema):
    class Meta:
        target = PaginationData
        register_as_scheme = True


class YtdlDownloadOptionsSchema(AnnotationSchema):
    class Meta:
        target = YtdlDownloadOptions
        register_as_scheme = True

    @post_load
    def into_instance(self, data, **kwargs):
        opts = YtdlDownloadOptions()
        opts.download_archive = data["download_archive"]
        opts.outtmpl = data["outtmpl"]
        return opts
