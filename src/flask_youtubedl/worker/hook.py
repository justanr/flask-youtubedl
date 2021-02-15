import logging
from datetime import datetime
from typing import Any, Dict

from injector import inject
from sqlalchemy.orm import Session

from ..core.hook import AbstractYtdlHook
from ..core.task import DownloadTask, DownloadTaskOnError
from ..models import Download, DownloadAttempt

logger = logging.getLogger(__name__)


class DownloadAttemptHook(AbstractYtdlHook):
    def __init__(self, attempt: DownloadAttempt, session: Session):
        self._attempt = attempt
        self._session = session
        super().__init__()

    def downloading(self, event: Dict[str, Any]) -> Any:
        self._attempt.set_downloading(event)
        self._session.commit()

    def error(self, event) -> Any:
        self._attempt.set_error("Download failed", datetime.utcnow())
        self._session.commit()

    def finished(self, event) -> Any:
        self._attempt.set_finished(datetime.utcnow())
        self._session.commit()

    def unknown(self, event) -> Any:
        logger.warning(f"Received unknown event {event!r}")


class DownloadAttemptHandleOnError(DownloadTaskOnError):
    def __init__(self, attempt: DownloadAttempt):
        self._attempt = attempt

    def on_error(self, task: DownloadTask, exception: Exception) -> None:
        if not self._attempt.is_canceled():
            self._attempt.set_error(f"Unhandled exception: {exception.__class__.__name__} {exception}", datetime.utcnow())


class TooManyFailedAttempts(DownloadTaskOnError):
    def __init__(self, download: Download,  max_failed_count: int = 3):
        self._download = download
        self._max_failed_count = max_failed_count

    def on_error(self, task: DownloadTask, exception: Exception) -> None:
        failed_attempts = [a for a in self._download.attempts if a.is_failed()]

        if len(failed_attempts) >= self._max_failed_count:
            self._download.block(
                "Too many failed attempts",
                when=datetime.utcnow(),
                propagate_to_latest_attempt=False,
            )
