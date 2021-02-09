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


def get_youtubedl_config_from_app_config(config, prefix="YTDL_", ytdl_config=None):
    if not prefix:
        raise Exception("Prefix not provided")

    normalized_prefix = prefix.lower()
    ytdl_config = ytdl_config or YoutubeDlConfiguration()
    raw_config = ytdl_config.__dict__

    for k, v in _get_configs(config, normalized_prefix):
        if k in raw_config:
            raw_config[k] = v

    if not getattr(config, "default_output_template", None):
        ytdl_config.default_output_template = DEFAULT_OUTTMPL

    return ytdl_config


def _get_configs(config, normalized_prefix):
    for k, v in config.items():
        lower_k = k.lower()
        if lower_k.startswith(normalized_prefix):
            yield (strip_prefix(normalized_prefix, lower_k)), v
