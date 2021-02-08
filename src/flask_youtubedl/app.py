import os
import typing as T
from pathlib import Path

from flask import Flask
from flask_injector import FlaskInjector

from . import extensions, server
from .config import CFG_PATH_TYPE, config_from_env, config_from_path, get_qualname
from .modules import FytdlModule
from .server import FytdlBlueprint


def make_app(
    config_path: T.Optional[CFG_PATH_TYPE], instance_path: T.Optional[CFG_PATH_TYPE]
) -> Flask:
    app = Flask("flask-youtubedl", instance_path=instance_path)
    setup_instance_path(app)
    configure_app(app, config_path)
    initialize_extensions(app)
    register_blueprints(app)
    finalize(app)
    return app


def setup_instance_path(app: Flask) -> None:
    if not app.instance_path:
        return

    instance_path = Path(app.instance_path)
    if not instance_path.exists():
        instance_path.mkdir()


def configure_app(app: Flask, config_path: T.Optional[CFG_PATH_TYPE]) -> None:
    if config_path:
        config_path = Path(config_path)

    # track these help debug configuration issues
    sources = app.config["__CONFIG_SOURCES"] = {
        "DEFAULT": "flask_youtubedl.config.DefaultConfiguration",
        "ENVVAR": "FYTDL_SETTINGS",
        "CONFIG_PATH": config_path,
        "ENVVAR_PREFIX": "FYTDL_",
        "MATCHED_ENVVARS": (),
    }

    app.config.from_object(app.config["__CONFIG_SOURCES"]["DEFAULT"])

    cfg = config_from_path(app, config_path)
    if cfg is not None:
        if isinstance(cfg, CFG_PATH_TYPE):
            sources["CONFIG_PATH"] = str(cfg)
            app.config.from_pyfile(cfg)
        else:
            sources["CONFIG_PATH"] = get_qualname(cfg)
            app.config.from_object(cfg)

    # should the envvar take precedence over a start script?
    app.config.from_envvar(sources["ENVVAR"], silent=True)
    # store whatever was actually in the real envvar
    original_envvar_source_value = sources["ENVVAR"]
    sources["ENVVAR"] = os.environ.get(sources["ENVVAR"])

    envvars = config_from_env(
        sources["ENVVAR_PREFIX"], ignore=frozenset(original_envvar_source_value)
    )
    app.config.update(envvars)
    sources["MATCHED_ENVVARS"] = tuple(envvars.keys())


def initialize_extensions(app: Flask) -> None:
    extensions.db.init_app(app)


def register_blueprints(app: Flask) -> None:
    bps = [
        bp
        for bp in server.blueprints.__dict__.values()
        if isinstance(bp, FytdlBlueprint)
    ]

    for bp in bps:
        app.register_blueprint(bp)


def finalize(app: Flask) -> None:
    injector = FlaskInjector(app, modules=FytdlModule.__subclasses__())
    app.injector = injector.injector
