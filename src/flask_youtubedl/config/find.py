import ast
import os
import re
import typing as T
from pathlib import Path
from types import ModuleType

from flask import Flask
from werkzeug.utils import ImportStringError, import_string

from ..exceptions import FlaskYoutubeDLException

# not 100% but good enough
__QUALNAME_RE = re.compile(r"^([_a-zA-Z]\w+\.?)+$")
__DEFAULT_CONFIG_FILENAME = "fytdl.cfg"

CFG_PATH_TYPE = T.Union[str, Path]


class ConfigurationError(FlaskYoutubeDLException):
    pass


def config_from_path(app: Flask, path: T.Optional[CFG_PATH_TYPE]) -> T.Union[Path, object]:
    if path is None:
        return root_around(app, __DEFAULT_CONFIG_FILENAME)

    if isinstance(path, str) and is_qualname(path):
        try:
            return import_string(path)
        except ImportStringError as e:
            raise ConfigurationError(f"Could not configure from import {path}") from e

    path = Path(path)
    if path.absolute().exists():
        return path.absolute()

    cfg = root_around(app, path)

    if cfg is None:
        raise ConfigurationError(f"Could not configure from file {path}")

    return cfg


def root_around(app: Flask, filename: CFG_PATH_TYPE) -> T.Optional[Path]:
    return find_in_project_path(filename) or look_in_instance_path(app, filename)


def find_in_project_path(filename: CFG_PATH_TYPE) -> T.Optional[Path]:
    here = _here()

    dir = here.parent

    for _ in range(2):
        dir = dir.parent
        cfg = dir / filename
        if cfg.exists():
            return cfg

    cfg = here / filename
    if cfg.exists():
        return cfg


def look_in_instance_path(app: Flask, filename: CFG_PATH_TYPE) -> T.Optional[Path]:
    cfg = Path(app.instance_path) / filename
    if cfg.exists():
        return cfg


def is_qualname(path: str) -> bool:
    return bool(__QUALNAME_RE.match(path))


def get_qualname(obj):
    if isinstance(obj, ModuleType):
        return obj.__package__

    return ".".join([obj.__module__, obj.__qualname__])


def config_from_env(prefix: str, ignore=frozenset()) -> T.Dict[str, T.Any]:
    config = {}
    for key, value in os.environ.items():
        if key in ignore:
            continue

        if key.startswith(prefix):
            try:
                value = ast.literal_eval(value)
                config[key.replace(prefix, "")] = value
            except Exception:
                pass

    return config


def _here() -> Path:
    return Path(os.path.dirname(__file__))
