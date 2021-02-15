import typing as T

from ..exceptions import FlaskYoutubeDLException

try:
    str.removeprefix
    strip_prefix = str.removeprefix
except AttributeError:

    def strip_prefix(prefix: str, key: str) -> str:
        return (key[len(prefix) :] if key.startswith(prefix) else key).lower()


class MissingPrefix(FlaskYoutubeDLException):
    pass


class MissingConfiguration(FlaskYoutubeDLException):
    pass


C = T.TypeVar("C")


def hydrate_config_from_app_config(*, app_config, this_config: C, prefix: str) -> C:
    if not prefix:
        raise MissingPrefix()

    if not app_config:
        raise MissingConfiguratio("app_config")

    if not this_config:
        raise MissingConfiguration("this_config")

    normalized_prefix = prefix.lower()
    raw_config = this_config.__dict__
    config_props = _get_config_props(this_config.__class__)

    for k, v in _get_config_values(app_config, normalized_prefix):
        if (prop := config_props.get(k)) :
            raw_config[prop] = v

    return this_config

def _get_config_props(config_type: T.Type[C]) -> T.Dict[str, str]:
    return {
        k.lower(): k
        for k in config_type.__dict__
        if not k.startswith("_") and not callable(k)
    }


def _get_config_values(config, normalized_prefix: str):
    for k, v in config.items():
        lower_k = k.lower()
        if lower_k.startswith(normalized_prefix):
            yield (strip_prefix(normalized_prefix, lower_k), v)
