from typing import Dict
from celery import group
from celery.exceptions import Reject
from ..extensions import celery
from ..models import Download
from sqlalchemy.orm import Session

__all__ = ("process_video_download",)

import logging
logger = logging.getLogger(__name__)

@celery.task(bind=True)
def process_video_download(self, download_id: str) -> None:
    session = self.injector.get(Session)
    print(repr(session))
    dl = Download.query.filter(Download.download_id == download_id).first()
    if not dl:
        print(f"No download record found for {download_id}")
        return

    print(f"Found download record {dl.download_id} for video {dl.video.name}")


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
