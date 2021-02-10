import logging
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from typing import Any, Callable, Dict, List

from injector import inject
from youtube_dl import YoutubeDL
from youtube_dl.utils import YoutubeDLError

from .configuration import OptionsFactory
from .ytdl_factory import YtdlFactory

logger = logging.getLogger(__name__)


class DownloadTaskOptionsFixer(OptionsFactory):
    __no_bind__ = True

    def reconfigure(self, video_options: Dict[str, Any]) -> Dict[str, Any]:
        video_options["logger"] = logger
        video_options["noplaylist"] = False
        video_options["progress_with_new_line"] = True
        video_options.setdefault("download_archive", "default_archive")

class DownloadTask:
    @inject
    def __init__(
        self,
        url: str,
        run_options: Dict[str, Any],
        ytdl_factory: YtdlFactory,
        options_factories: List[OptionsFactory],
    ):
        self._url = url
        self._run_options = run_options
        self._options_factories = options_factories
        self._options_factories.append(DownloadTaskOptionsFixer())
        self._ytdl_factory = ytdl_factory
        self._ytdl = None
        self._options = None

    @property
    def ytdl(self):
        ytdl = self._ytdl

        if ytdl is None:
            ytdl = self._ytdl = self._ytdl_factory(**self.options)

        return ytdl

    @property
    def options(self):
        options = self._options
        if options is None:
            for fixer in self._options_factories:
                fixer(self._run_options)

            options = self._options = self._run_options

        return options

    def run(self):
        with self.ytdl as ytdl:
            try:
                ytdl.download([self._url])
            except (YoutubeDLError) as e:
                # ???
                pass

    def is_playlist(self):
        return self.info.get("_type") == "playlist"
