from .utils import safe_render_to, upload_file
from fabric import task
from .context.app import QueueTypes
from .context import Context, Config
from typing import cast
import fabric.connection


def generate(c: Context, template: str = "celery") -> None:
    if c.app.queue != QueueTypes.CELERY:
        return
    app_file = c.app.local_dir / "celery.conf"
    t = c.config.dirs.local.template / "celery" / f"{template}.jinja2"
    safe_render_to(c, t, app_file)


def deploy(c: Context) -> None:
    if c.app.queue != QueueTypes.CELERY:
        return
    app_file = c.app.local_dir / "celery.conf"
    c.sh.upload_etc(c.app, app_file, f"/etc/celery/{c.app.project.name}.conf")
    activate(c)


def activate(c: Context) -> None:
    if c.app.queue != QueueTypes.CELERY:
        return
    c.sh.systemd("reload")
    c.sh.systemd("enable", f"celery@{c.app.project.name}.service")
    c.sh.systemd("enable", f"celerybeat@{c.app.project.name}.service")
    c.sh.systemd("restart", f"celery@{c.app.project.name}.service")
    c.sh.systemd("restart", f"celerybeat@{c.app.project.name}.service")


def setup(c: Context) -> None:
    if c.app.queue != QueueTypes.CELERY:
        return
    generate(c)
    deploy(c)
    activate(c)


@task
def sync(c):
    # type: (fabric.connection.Connection) -> None
    # FIXME c.put('./celery', '/etc', use_sudo=True)
    c.sudo("systemctl daemon-reload")


@task
def sync_services(c):
    # type: (fabric.connection.Connection) -> None
    config = Config.config_from_conection(c)
    c_dir = config.dirs.local.template / "celery"
    upload_file(c, c_dir / "celery@.service", "/etc/systemd/system")
    upload_file(c, c_dir / "celerybeat@.service", "/etc/systemd/system")
    upload_file(c, c_dir / "celery.service", "/etc/systemd/system")
    upload_file(c, c_dir / "celerybeat.service", "/etc/systemd/system")
    upload_file(c, c_dir / "celery.tmpfiles", "/etc/tmpfiles.d/celery.conf")

    c.sudo("systemctl daemon-reload")
