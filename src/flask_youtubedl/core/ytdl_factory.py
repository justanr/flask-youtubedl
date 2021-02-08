from abc import ABC, abstractmethod
from typing import Any, Dict

from youtube_dl import YoutubeDL

from .download_archive import DownloadArchiveFactory, UseArchiveMixin
from injector import inject

class ArchivalYoutubeDl(UseArchiveMixin, YoutubeDL):
    """
    YoutubeDL that uses an external archive
    """

    pass


class YtdlFactory(ABC):
    @abstractmethod
    def get(self, **params: Dict[str, Any]) -> YoutubeDL:
        raise NotImplementedError()

    def __call__(self, **params: Dict[str, Any]) -> YoutubeDL:
        return self.get(**params)


class ArchivalYoutubeDlFactory(YtdlFactory):
    @inject
    def __init__(self, archive_factory: DownloadArchiveFactory) -> None:
        self._archive_factory = archive_factory

    def get(self, **params: Dict[str, Any]) -> YoutubeDL:
        return ArchivalYoutubeDl(params, archive=self._archive_factory.get())
