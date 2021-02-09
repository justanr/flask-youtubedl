from injector import inject
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from youtube_dl.utils import DEFAULT_OUTTMPL
from ..config import YoutubeDlConfiguration


class OptionsFactory(ABC):
    @abstractmethod
    def reconfigure(self, video_options: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError()

    def __call__(self, video_options: Dict[str, Any]) -> Dict[str, Any]:
        return self.reconfigure(video_options)


class OptionsFixer(OptionsFactory):
    @inject
    def __init__(self, configuration: YoutubeDlConfiguration):
        self._configuration = configuration

    def reconfigure(self, video_options: Dict[str, str]) -> Dict[str, str]:
        these_configs = video_options.copy()
        outtmpl = these_configs.get("outtmpl")

        if not outtmpl:
            outtmpl = self._configuration.default_output_template

        if not outtmpl.startswith("/"):
            outtmpl = f"{self._configuration.base_download_path}/{outtmpl}"

        these_configs["outtmpl"] = outtmpl

        these_configs.setdefault(
            "download_archive", self._configuration.download_archive
        )

        return these_configs
