from abc import ABC, abstractmethod
from typing import Any, Dict, List

from youtube_dl import YoutubeDL

from .download_archive import DownloadArchiveFactory, UseArchiveMixin
from .configuration import OptionsFactory
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
    def __init__(self, archive_factory: DownloadArchiveFactory, options_factories: List[OptionsFactory]) -> None:
        self._archive_factory = archive_factory
        self._options_factories = options_factories

    def get(self, **params: Dict[str, Any]) -> YoutubeDL:
        for factory in self._options_factories:
            factory.reconfigure(params)
        return ArchivalYoutubeDl(params, archive=self._archive_factory.get())
