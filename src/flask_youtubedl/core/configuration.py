import os
from typing import Optional

from youtube_dl.utils import DEFAULT_OUTTMPL

try:
    str.removeprefix
    strip_prefix = str.removeprefix
except AttributeError:

    def strip_prefix(prefix: str, key: str) -> str:
        return (key[len(prefix) :] if key.startswith(prefix) else key).lower()

class YoutubeDlConfiguration:
    download_archive: Optional[str] = None
    base_download_path: str = "/var/run/fytdl/downloads"
    default_output_template: str = DEFAULT_OUTTMPL


def get_config_from_env(prefix="FYTDL_") -> YoutubeDlConfiguration:
    config = YoutubeDlConfiguration()
    our_configs = {
        strip_prefix(prefix, k): v
        for k, v in os.environ.items()
        if k.startswith(prefix)
    }

    for k, v in our_configs.items():
        if k in config.__dict__:
            config.__dict__[k] = v

    if not getattr(config, "default_output_template"):
        config.default_output_template = DEFAULT_OUTTMPL

    return config


