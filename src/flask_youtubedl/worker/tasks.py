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
from .task import DownloadTask

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")

app = Celery("tasks", backend=f"redis://{REDIS_HOST}", broker=f"pyamqp://guest@{RABBIT_HOST}")


class Ytdl(UseArchiveMixin, YoutubeDL):
    pass


class OptionsFixer:
    def __init__(self, configuration: YoutubeDlConfiguration):
        self._configuration = configuration

    def fix_configs(self, video_options: Dict[str, str]) -> Dict[str, str]:
        these_configs = video_options.copy()
        outtmpl = these_configs.get("outtmpl")

        if not outtmpl:
            outtmpl = self._configuration.default_output_template

        if not  outtmpl.startswith("/"):
            outtmpl = f"{self._configuration.base_download_path}/{outtmpl}"

        these_configs["outtmpl"] = outtmpl

        these_configs.setdefault("download_archive", self._configuration.download_archive)

        return these_configs

    def __call__(self, video_options: Dict[str, str]) -> Dict[str, str]:
        return self.fix_configs(video_options)


def ytdl_factory(options):
    return Ytdl(options, archive=RedisDownloadArchive(redis.Redis(host=REDIS_HOST)))


CONFIGURATION = get_config_from_env()
FIXER = OptionsFixer(CONFIGURATION)

@app.task(bind=True)
def download(self, url, video_options: Dict[str, str] = None):
    options = make_options(video_options)

    dl_task = DownloadTask(url, ytdl_factory, lambda: FIXER(video_options))

    looks_like_playlist = "playlist" in url

    if dl_task.is_playlist():
        videos = [v["webpage_url"] for v in dl_task.info["entries"]]
        downloads = group(download.s(v, video_options) for v in videos)
        downloads.delay()
    else:
        dl_task.run()
        print(f"Got options: {repr(options)}")
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
