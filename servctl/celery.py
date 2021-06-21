from .utils import safe_render_to
from .context.app import QueueTypes
from .context import Context, ContextWithApp
from .commands import register as cmd_register


def generate(c: ContextWithApp, template: str = "celery") -> None:
    if c.app.queue != QueueTypes.CELERY:
        return
    app_file = c.app.local_dir / "celery.conf"
    t = c.config.dirs.local.template / "celery" / f"{template}.jinja2"
    safe_render_to(c, t, app_file)


def deploy(c: ContextWithApp) -> None:
    if c.app.queue != QueueTypes.CELERY:
        return
    app_file = c.app.local_dir / "celery.conf"
    c.sh.upload_etc(c.app, app_file, f"/etc/celery/{c.app.project.name}.conf")
    activate(c)


def activate(c: ContextWithApp) -> None:
    if c.app.queue != QueueTypes.CELERY:
        return
    c.sh.systemd("reload")
    c.sh.systemd("enable", f"celery@{c.app.project.name}.service")
    c.sh.systemd("enable", f"celerybeat@{c.app.project.name}.service")
    c.sh.systemd("restart", f"celery@{c.app.project.name}.service")
    c.sh.systemd("restart", f"celerybeat@{c.app.project.name}.service")


def setup(c: ContextWithApp) -> None:
    if c.app.queue != QueueTypes.CELERY:
        return
    generate(c)
    deploy(c)
    activate(c)


@cmd_register(name="celery:register")
def register(c: Context) -> None:
    c_dir = c.config.dirs.local.template / "celery"
    c.sh.upload(c_dir / "celery@.service", "/etc/systemd/system")
    c.sh.upload(c_dir / "celerybeat@.service", "/etc/systemd/system")
    c.sh.upload(c_dir / "celery.service", "/etc/systemd/system")
    c.sh.upload(c_dir / "celerybeat.service", "/etc/systemd/system")
    c.sh.upload(c_dir / "celery.tmpfiles", "/etc/tmpfiles.d/celery.conf")

    c.sh.systemd("reload")
