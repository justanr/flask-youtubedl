import logging
import logging.config
import os
import sys
import typing as T
from pathlib import Path

from celery.signals import setup_logging
from celery import Celery
from flask import Flask
from flask_injector import FlaskInjector

from . import config, extensions, server
from .modules import FytdlModule
from .server import FytdlBlueprint


def make_app(
    config_path: T.Optional[config.CFG_PATH_TYPE],
    instance_path: T.Optional[config.CFG_PATH_TYPE],
    envvar_prefixes=(),
) -> Flask:
    app = Flask("flask-youtubedl", instance_path=instance_path)
    setup_instance_path(app)
    configure_app(app, config_path, envvar_prefixes)
    configure_logging(app)
    configure_celery_app(app, extensions.celery)
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


def configure_app(
    app: Flask, config_path: T.Optional[config.CFG_PATH_TYPE], envvar_prefixes=()
) -> None:
    if config_path:
        config_path = Path(config_path)

    # track these help debug configuration issues
    sources = app.config["__CONFIG_SOURCES"] = {
        "DEFAULT": "flask_youtubedl.config.DefaultConfiguration",
        "ENVVAR": "FYTDL_SETTINGS",
        "CONFIG_PATH": config_path,
        "ENVVAR_PREFIXES": ["FYTDL_", "YTDL_"],
        "MATCHED_ENVVARS": (),
    }

    sources["ENVVAR_PREFIXES"].extend(envvar_prefixes)

    app.config.from_object(app.config["__CONFIG_SOURCES"]["DEFAULT"])

    cfg = config.config_from_path(app, config_path)
    if cfg is not None:
        if isinstance(cfg, (str, Path)):
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

    for prefix in sources["ENVVAR_PREFIXES"]:
        envvars = config.config_from_env(
            prefix, ignore=frozenset(original_envvar_source_value)
        )
        app.config.update(envvars)
        sources["MATCHED_ENVVARS"] += tuple(envvars.keys())

    ytdl_config = app.config["YTDL"] = config.YoutubeDlConfiguration()

    for prefix in sources["ENVVAR_PREFIXES"]:
        config.get_youtubedl_config_from_app_config(app.config, prefix, ytdl_config)


def configure_logging(app: Flask) -> None:
    log_level = "INFO"

    if app.testing:
        _configure_test_logging(app)

    if app.debug:
        log_level = "DEBUG"

    config = {
        "version": 1,
        "filters": {"exclude_errors": {"()": "flask_youtubedl.logging.ExcludeErrorLogFilter"}},
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "stream": sys.stdout,
                "filters": ["exclude_errors"],
            },
            "stderr": {
                "class": "logging.StreamHandler",
                "level": "ERROR",
                "stream": sys.stderr,
            },
        },
        "root": {"level": "NOTSET", "handlers": ["stdout", "stderr"]},
    }

    app.config["LOGGING_CONFIG"] = config

    logging.config.dictConfig(config)


def _configure_test_logging(app: Flask) -> None:
    pass


def configure_celery_app(app: Flask, celery: Celery) -> None:
    flat_celery_config = app.config.get_namespace("CELERY_")
    celery_ns = {}

    for (key, value) in flat_celery_config.items():
        if key != "config":
            celery_ns[key] = value
            try:
                del app.config[f"CELERY_{key.upper()}"]
            except KeyError:
                pass

    celery_ns.update(app.config.get("CELERY_CONFIG"))
    celery.conf.update(celery_ns)
    app.config["CELERY_CONFIG"] = celery_ns

    TaskBase = celery.Task

    class ContextTask(TaskBase):
        def __call__(self, *args, **kwargs):
            self.injector = app.injector
            with app.app_context():
                return super().__call__(*args, **kwargs)

    celery.Task = ContextTask

    @setup_logging.connect
    def configure_logging(*args, **kwargs):
        logging.config.dictConfig(app.config["LOGGING_CONFIG"])


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
