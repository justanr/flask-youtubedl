from marshmallow import fields as ma_fields
from marshmallow_annotations import AnnotationSchema

from ..models import Playlist, Video, Download, DownloadAttempt


class PlaylistSchema(AnnotationSchema):
    videos = ma_fields.List(ma_fields.Nested("VideoSchema", exclude=("playlists",)))

    class Meta:
        target = Playlist
        register_as_scheme = True


class VideoSchema(AnnotationSchema):
    downloads = ma_fields.List(ma_fields.Nested("DownloadSchema", exclude=("video", "video_id")))

    class Meta:
        target = Video
        register_as_scheme = True

        class Fields:
            playlists = {"exclude": ("videos",)}

class DownloadSchema(AnnotationSchema):
    attempts = ma_fields.List(ma_fields.Nested("DownloadAttemptsSchema", exclude=("download", "download_id")))

    class Meta:
        target = Download
        register_as_scheme = True

        class Fields:
            video = {"exclude": ("downloads",)}

class DownloadAttemptsSchema(AnnotationSchema):
    class Meta:
        target = DownloadAttempt
        register_as_scheme = True

        class Fields:
            download = {"exclude": ("attempts",)}
