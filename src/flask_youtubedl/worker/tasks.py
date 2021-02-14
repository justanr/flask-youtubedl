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
from .hook import (
    DownloadAttemptHandleOnError,
    DownloadAttemptHook,
    TooManyFailedAttempts,
)

__all__ = ("process_video_download",)

logger = logging.getLogger(__name__)


@celery.task(bind=True)
def process_video_download(self, download_id: str) -> None:
    session = self.injector.get(Session)

    try:
        dl = Download.query.filter(Download.download_id == download_id).first()
    except Exception as e:
        logger.exception(
            f"Unhandled exception while attempting to retrieve download {download_id}"
        )

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

    attempt = dl.latest_attempt

    if not attempt or attempt.is_failed():
        attempt = dl.start_new_attempt()
        session.add(attempt)

    if dl.options:
        try:
            options = json.loads(dl.options)
        except Exception as e:
            dl.block(
                "Could not decode provided options: {dl.options}",
                when=datetime.utcnow(),
                propagate_to_latest_attempt=True,
            )
            session.commit()
            return

    progress_hooks = options.setdefault("progress_hooks", [])
    progress_hooks.append(DownloadAttemptHook(attempt, session))
    task_factory = self.injector.get(ClassAssistedBuilder[DownloadTask])
    task = task_factory.build(
        url=dl.video.webpage_url,
        run_options=options,
        on_error=[DownloadAttemptHandleOnError(attempt), TooManyFailedAttempts(dl, 3)],
    )

    task.run()

    session.commit()
    session.close()
