from .hook import YtdlHook
from .logger import YtdlLogger
from youtube_dl import YoutubeDL
from typing import Callable

class DownloadTask:
    def __init__(self, url: str,  ytdl_factory: Callable[[dict], YoutubeDL], options: dict):
        self._url = url
        self._options = options or {}
        self._ytdl_factory = ytdl_factory
        self._hook = YtdlHook(None)

    def run(self):
        self.intercept_options()
        with self._ytdl_factory(self._options) as ytdl:
            self._hook = ytdl.extract_info(self._url, download=False)
            ytdl.download(self._url)


    def intercept_options(self):
        self._options['logger'] = YtdlLogger

        self._options.setdefault('progress_hooks').append(self._hook)
        self._options["noplaylist"} = False
        self._options["progress_with_new_line"] = True
