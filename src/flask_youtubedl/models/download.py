from datetime import datetime
from typing import Any, Dict, Optional

from ..extensions import db
from .base import BaseModel
from .video import Video


class Download(BaseModel, db.Model):
    __tablename__ = "downloads"

    # uuid -- store as string for prototyping
    download_id: str = db.Column(db.Text)
    # json blob, just store as str for now, it won't be queried
    options: str = db.Column(db.Text, default="{}")
    block_further: bool = db.Column(db.Boolean, default=False)
    block_reason: str = db.Column(db.Text, nullable=True)

    # video can have multiple downloads
    video_id: int = db.Column(db.Integer, db.ForeignKey("videos.id"))
    video: Video = db.relationship(Video, backref=db.backref("downloads", lazy=True))

    @property
    def latest_attempt(self) -> Optional["DownloadAttempt"]:
        if self.attempts:
            return self.attempts[-1]
        return None

    def start_new_attempt(self) -> "DownloadAttempt":
        attempt = DownloadAttempt()
        attempt.download = self
        return attempt

    def block(
        self, reason: str, when: datetime, propagate_to_latest_attempt=True
    ) -> None:
        self.block_further = True
        self.block_reason = f"Blocked at {when}: {reason}"

        if propagate_to_latest_attempt and (attempt := dl.latest_attempt):
            attempt.set_error(reason, when)


class DownloadAttempt(BaseModel, db.Model):
    __tablename__ = "download_attempts"
    tmpfilename: str = db.Column(db.Text, nullable=True)
    filename: str = db.Column(db.Text, nullable=True)
    total_bytes: int = db.Column(db.BigInteger, nullable=True)
    downloaded_bytes: int = db.Column(db.BigInteger, nullable=True)
    # seconds, best guess, can be none
    eta: int = db.Column(db.Integer, nullable=True)
    # seconds since download started, none if it hasn't started
    elapsed: float = db.Column(db.Float, nullable=True)
    # bytes/second, can be None
    speed: float = db.Column(db.Float, nullable=True)
    status: str = db.Column(db.Text, default="Pending")
    # how to handle these if/when they occur?
    # fragment_index
    # fragment_count
    message: str = db.Column(db.Text, nullable=True)
    download_id: int = db.Column(db.Integer, db.ForeignKey("downloads.id"))
    download: Download = db.relationship(
        Download, backref=db.backref("attempts", lazy=True)
    )

    def is_failed(self) -> bool:
        return self.status.lower() == "error"

    def is_finished(self) -> bool:
        return self.status.lower() == "finished"

    def is_downloading(self) -> bool:
        return self.status.lower() == "downloading"

    def is_pending(self) -> bool:
        return self.status.lower() == "pending"

    def set_error(self, error_message: str, when: datetime) -> None:
        self.status = "Error"
        self.message = f"Failed at {when}: {error_message}"

    def set_finished(self, when: datetime) -> None:
        self.status = "Finished"
        self.message = f"Finished at {when}"

    def set_downloading(self, info: Dict[str, Any]) -> None:
        self._update_attempt_attribute("downloaded_bytes", info)
        self._update_attempt_attribute("total_bytes", info)
        self._update_attempt_attribute("eta", info)
        self._update_attempt_attribute("speed", info)
        self._update_attempt_attribute("elapsed", info)
        self._update_attempt_attribute("filename", info)
        self._update_attempt_attribute("tmpfilename", info)
        self.status = "Downloading"

    def _update_attempt_attribute(self, attr_name, event):
        existing_value = getattr(self, attr_name, None)
        event_value = event.get(attr_name)

        value = event_value if event_value is not None else existing_value
        setattr(self, attr_name, value)
