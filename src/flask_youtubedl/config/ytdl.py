from typing import Optional

from youtube_dl.utils import DEFAULT_OUTTMPL

from .helpers import hydrate_config_from_app_config


class YoutubeDlConfiguration:
    download_archive: Optional[str] = None
    base_download_path: str = "/var/run/fytdl/downloads"
    default_output_template: str = DEFAULT_OUTTMPL


def get_youtubedl_config_from_app_config(
    config, prefix="YTDL_", ytdl_config: YoutubeDlConfiguration = None
) -> YoutubeDlConfiguration:
    ytdl_config = ytdl_config if ytdl_config is not None else YoutubeDlConfiguration()

    hydrate_config_from_app_config(
        app_config=config, this_config=ytdl_config, prefix=prefix
    )

    if not getattr(ytdl_config, "default_output_template", None):
        ytdl_config.default_output_template = DEFAULT_OUTTMPL

    return ytdl_config
