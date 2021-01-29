from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from typing import Callable, Dict

from youtube_dl import YoutubeDL
from youtube_dl.utils import YoutubeDLError

from .hook import YtdlHook
from .logger import YtdlLogger


class DownloadTask:
    def __init__(
        self,
        url: str,
        ytdl_factory: Callable[[Dict[str, str]], YoutubeDL],
        options_factory: Callable[[], Dict[str, str]],
    ):
        self._url = url
        self._options_factory = (
            options_factory if options_factory is not None else lambda: {}
        )
        self._ytdl_factory = ytdl_factory
        self._hook = YtdlHook(None)
        self._stderr = StringIO()
        self._stdout = StringIO()
        self._ytdl = None
        self._options = None

    @property
    def ytdl(self):
        ytdl = self._ytdl

        if ytdl is None:
            ytdl = self._ytdl = self._ytdl_factory(self.options)

        return ytdl

    @property
    def options(self):
        options = self._options
        if options is None:
            options = self._options = self._options_factory()
            self._intercept_options()

        return options

    def run(self):
        self._reset_streams()
        with self.ytdl as ytdl:
            self.extract_info()
            try:
                ytdl.download([self._url])
            except (YoutubeDLError) as e:
                self._hook.exception(e)

        self._reset_streams()

    def extract_info(self):
        if self._hook.info is None:
            self._hook.info = self.ytdl.extract_info(self._url, download=False)

    @property
    def info(self):
        self.extract_info()
        return self._hook.info

    def is_playlist(self):
        return self.info.get("_type") == "playlist"

    def _intercept_options(self):
        self._options["logger"] = YtdlLogger
        self._set_hook()
        self._options["noplaylist"] = False
        self._options["progress_with_new_line"] = True


    def _set_hook(self):
        hooks = self._options.get("progress_hooks")
        hooks = [] if hooks is None else hooks
        hooks.append(self._hook)
        self._options["progress_hooks"] = hooks

    def _reset_streams(self):
        self._stderr.seek(0)
        self._stdout.seek(0)
