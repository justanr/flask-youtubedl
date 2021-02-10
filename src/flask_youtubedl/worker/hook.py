import logging
from datetime import datetime
from typing import Any, Dict

from injector import inject
from sqlalchemy.orm import Session

from ..core.hook import AbstractYtdlHook
from ..models import Download, DownloadAttempt

logger = logging.getLogger(__name__)


class DownloadAttemptHook(AbstractYtdlHook):
    def __init__(self, attempt: DownloadAttempt, session: Session):
        self._attempt = attempt
        self._session = session
        super().__init__()

    def downloading(self, event: Dict[str, Any]) -> Any:
        self._update_attempt_attribute("downloaded_bytes", event)
        self._update_attempt_attribute("total_bytes", event)
        self._update_attempt_attribute("eta", event)
        self._update_attempt_attribute("speed", event)
        self._update_attempt_attribute("elapsed", event)
        self._update_attempt_attribute("filename", event)
        self._update_attempt_attribute("tmpfilename", event)
        self._attempt.status = "Downloading"
        self._session.commit()

    def error(self, event) -> Any:
        self._attempt.status = "Error"
        self._attempt.error = f"Failed at {datetime.utcnow()}"
        self._session.commit()

    def finished(self, event) -> Any:
        self._attempt.status = "Finished"
        self._session.commit()

    def unknown(self, event) -> Any:
        logger.warning(f"Received unknown event {event!r}")

    def _update_attempt_attribute(self, attr_name, event):
        existing_value = getattr(self._attempt, attr_name, None)
        event_value = event.get(attr_name)

        value = event_value if event_value is not None else existing_value
        setattr(self._attempt, attr_name, value)
