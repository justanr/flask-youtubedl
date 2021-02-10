import json
import logging
from typing import Dict

from celery import group
from celery.exceptions import Reject
from injector import ClassAssistedBuilder
from sqlalchemy.orm import Session

from ..core.task import DownloadTask
from ..extensions import celery
from ..models import Download, DownloadAttempt
from .hook import DownloadAttemptHook

__all__ = ("process_video_download",)

logger = logging.getLogger(__name__)


@celery.task(bind=True)
def process_video_download(self, download_id: str) -> None:
    session = self.injector.get(Session)
    try:
        dl = Download.query.filter(Download.download_id == download_id).first()
    except Exception as e:
        logger.exception(f"Unhandled exception while attempting to retrieve download {download_id}")

    if not dl:
        logger.warn(f"No download record found for {download_id}")
        return

    logger.info(f"Found download record {dl.download_id} for video {dl.video.name}")

    if dl.block_further:
        msg = f"{dl.download_id} is blocked from further downloads"
        if dl.block_reason:
            msg = f"{msg}: {dl.block_reason}"
        logger.error(msg)
        return

    if dl.options:
        try:
            options = json.loads(dl.options)
        except Exception as e:
            dl.block_further = True
            dl.block_reason = "Could not decode provided options: {dl.options}"
            session.commit()
            return

    attempt = DownloadAttempt()
    attempt.download = dl
    session.add(attempt)
    session.commit()

    progress_hooks = options.setdefault("progress_hooks", [])
    progress_hooks.append(DownloadAttemptHook(attempt, session))
    task_factory = self.injector.get(ClassAssistedBuilder[DownloadTask])
    task = task_factory.build(url=dl.video.webpage_url, run_options=options)
    try:
        task.run()
    except Exception as e:
        logger.exception(
            f"Unhandled exception while downloading {dl.video.webpage_url}"
        )
        attempt.status = "Error"
        attempt.error = str(e)

    session.commit()
    session.close()


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
        "progress_hooks": [],
    }

    if video_options is not None:
        default_options.update(video_options)
    return default_options
