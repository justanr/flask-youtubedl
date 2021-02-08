from injector import provider, singleton
from youtube_dl import YoutubeDL

from ..core.configuration import (
    OptionsFactory,
    OptionsFixer,
    YoutubeDlConfiguration,
    get_config_from_env,
)
from ..core.download_archive import (
    DownloadArchiveFactory,
    LockedFileDownloadArchiveFactory,
)
from ..core.ytdl_factory import ArchivalYoutubeDlFactory, YtdlFactory
from ._helpers import FytdlModule


class YoutubeDLModule(FytdlModule):
    def configure(self, binder):
        binder.bind(YtdlFactory, ArchivalYoutubeDlFactory)
        binder.bind(OptionsFactory, OptionsFixer)

    @provider
    def provide_youtubedl(self, factory: YtdlFactory) -> YoutubeDL:
        return factory.get()

    @singleton
    @provider
    def provide_ytdl_configuration(self) -> YoutubeDlConfiguration:
        return get_config_from_env()

    @singleton
    @provider
    def provide_file_archive(
        self, config: YoutubeDlConfiguration
    ) -> DownloadArchiveFactory:
        return LockedFileDownloadArchiveFactory()
