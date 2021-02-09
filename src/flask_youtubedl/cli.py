import code
import os
import sys
from pprint import pprint

import click
from flask import current_app
from flask.cli import FlaskGroup, ScriptInfo, with_appcontext

from .app import make_app
from .extensions import celery, db

try:
    import IPython
    from traitlets.config import get_config

    def run_shell(banner, ctx):
        c = get_config()
        c.InteractiveShellEmbed.colors = "Linux"
        IPython.embed(config=c, banner1=banner, user_ns=ctx)


except ImportError:

    def run_shell(banner, ctx):
        code.interact(banner=banner, local=ctx)


def app_factory(script_info):
    config_file = getattr(script_info, "config_file", None)
    instance_path = getattr(script_info, "instance_path", None)
    return make_app(config_file, instance_path)


def set_(attr_name):
    def _(ctx, param, value):
        script_info = ctx.ensure_object(ScriptInfo)
        setattr(script_info, attr_name, value)

    return _


class FytdlGroup(FlaskGroup):
    pass


@click.group(
    cls=FytdlGroup,
    create_app=app_factory,
    add_version_option=False,
    invoke_without_command=True,
)
@click.option(
    "-c",
    "--config",
    expose_value=False,
    callback=set_("config_file"),
    required=False,
    is_flag=False,
    is_eager=True,
    metavar="CONFIG",
    help="Specify the config file to use, accepts either a file path or module notation",
)
@click.option(
    "-i",
    "--instance-path",
    expose_value=False,
    callback=set_("instance_path"),
    required=False,
    is_flag=False,
    is_eager=True,
    metavar="INSTANCE_PATH",
    help="Specify the instance path to use",
)
@click.pass_context
def fytdl(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@fytdl.command(
    "celery",
    add_help_option=False,
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.pass_context
@with_appcontext
def start_celery(ctx):
    celery.start(ctx.args)


@fytdl.command("shell", short_help="Runs a shell within an flask-youtubedl context")
@with_appcontext
def shell_command():
    banner = f"Python {sys.version} on {sys.platform}\nInstance Path {current_app.instance_path}"

    ctx = {"db": db, "app": current_app, "injector": current_app.injector}

    startup = os.environ.get("PYTHONSTARTUP")
    if startup and os.path.is_file(startup):
        with open(startup, "r") as fh:
            eval(compile(fh.read(), startup, "exec"), ctx)

    ctx.update(current_app.make_shell_context())

    run_shell(banner, ctx)


@fytdl.command("show-config", add_help_option=False)
def show_config():
    pprint(dict(current_app.config))
