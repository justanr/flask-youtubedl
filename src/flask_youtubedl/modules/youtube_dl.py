import logging
from typing import List

from flask.config import Config
from injector import Injector, provider, singleton
from youtube_dl import YoutubeDL

from ..core.configuration import OptionsFactory, OptionsFixer, YoutubeDlConfiguration
from ..core.download_archive import (
    DownloadArchive,
    DownloadArchiveFactory,
    GenericeDownloadArchiveFactory,
    LockedFileDownloadArchive,
    RedisDownloadArchive,
    RedisDownloadArchiveFactory,
    SetDownloadArchive,
)
from ..core.ytdl_factory import ArchivalYoutubeDlFactory, YtdlFactory
from ._helpers import FytdlModule

logger = logging.getLogger(__name__)

class YoutubeDLModule(FytdlModule):
    _ARCHIVE_PROVIDER_MAP = {
        "file": lambda _: GenericeDownloadArchiveFactory(LockedFileDownloadArchive),
        "set": lambda _: GenericeDownloadArchiveFactory(SetDownloadArchive),
        "redis": lambda i: i.get(RedisDownloadArchiveFactory),
    }

    def configure(self, binder):
        binder.bind(YtdlFactory, ArchivalYoutubeDlFactory)
        binder.multibind(
            List[OptionsFactory],
            to=[
                impl
                for impl in OptionsFactory.__subclasses__()
                if not getattr(impl, "__no_bind__", False)
            ],
        )

    @provider
    def provide_youtubedl(self, factory: YtdlFactory) -> YoutubeDL:
        return factory.get()

    @singleton
    @provider
    def provide_ytdl_configuration(self, app_config: Config) -> YoutubeDlConfiguration:
        return app_config["YTDL"]

    @singleton
    @provider
    def provide_download_archive_factory(
        self, config: Config, injector: Injector
    ) -> DownloadArchiveFactory:
        archive_provider_name = (config.get("ARCHIVE_PROVIDER") or "file").lower()
        archive_provider = self._ARCHIVE_PROVIDER_MAP.get(
            archive_provider_name, self._ARCHIVE_PROVIDER_MAP["file"]
        )
        logger.info(f"Using archive provider: {archive_provider}")
        return archive_provider(injector)

    @provider
    def provide_download_archive(
        self, factory: DownloadArchiveFactory
    ) -> DownloadArchive:
        return factory.get()
