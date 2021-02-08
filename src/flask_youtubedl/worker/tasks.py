import os
from collections import ChainMap
from functools import partial
from typing import Dict

import redis
from celery import Celery, group
from celery.exceptions import Reject
from youtube_dl import YoutubeDL

from ..core.configuration import YoutubeDlConfiguration, get_config_from_env
from ..core.download_archive import RedisDownloadArchive, UseArchiveMixin
from ..hook import AbstractYtdlHook
from ..task import DownloadTask

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")

app = Celery(
    "tasks", backend=f"redis://{REDIS_HOST}", broker=f"pyamqp://guest@{RABBIT_HOST}"
)

__all__ = ("download",)


class Ytdl(UseArchiveMixin, YoutubeDL):
    pass


class DatabaseHook(AbstractYtdlHook):
    def __init__(self, dl_entry):
        self._dl = dl_entry
        super().__init__()

    def downloading(self, event):
        # update DB w/ progress
        pass

    def error(self, event):
        # update DB w/ status failed && create log?
        pass

    def finished(self, event):
        # update DB w/ status finished
        pass

    def unknown(self, event):
        # drop it
        pass


def ytdl_factory(options):
    return Ytdl(options, archive=RedisDownloadArchive(redis.Redis(host=REDIS_HOST)))


CONFIGURATION = get_config_from_env()
FIXER = OptionsFixer(CONFIGURATION)


@app.task(bind=True)
def process_video_download(download_id: str) -> None:
    dl = Download.query.where(Download.download_id == download_id).first()
    if not dl:
        # log error
        return

    options = json.loads(dl.options or "{}")

    video_url = dl.video.webage_url

    # get download info + video details from database
    # invoke download(url, options)
    pass


def download(url, video_options: Dict[str, str] = None):
    options = make_options(video_options)

    dl_task = DownloadTask(url, ytdl_factory, lambda: FIXER(video_options))

    looks_like_playlist = "playlist" in url

    if dl_task.is_playlist():
        videos = [v["webpage_url"] for v in dl_task.info["entries"]]
        downloads = group(download.s(v, video_options) for v in videos)
        downloads.delay()
    else:
        dl_task.run()
        return dl_task._hook.final_state


def make_options(video_options: Dict[str, str] = None):
    default_options = {
        "quiet": True,
        "download_archive": "dlarchive",
        "outtmpl": "%(title)s.%(ext)s",
    }

    if video_options is not None:
        default_options.update(video_options)

    return default_options
