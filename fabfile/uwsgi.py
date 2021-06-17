from .context import Context
from .context.app import WsgiTypes
from .utils import safe_render_to


def generate(c: Context, template: str = "django") -> None:
    if not c.app.wsgi or c.app.wsgi.type != WsgiTypes.UWSGI:
        return
    app_file = c.app.local_dir / "uwsgi.ini"
    t = c.config.dirs.local.template / "uwsgi" / "apps-available" / f"{template}.jinja2"
    safe_render_to(c, t, app_file)


def deploy(c: Context) -> None:
    if not c.app.wsgi or c.app.wsgi.type != WsgiTypes.UWSGI:
        return
    app_file = c.app.local_dir / "uwsgi.ini"
    c.sh.upload_etc(c.app, app_file, f"/etc/uwsgi/apps-enabled/{c.app.project.name}.ini")
    activate(c)


def activate(c: Context) -> None:
    if not c.app.wsgi or c.app.wsgi.type != WsgiTypes.UWSGI:
        return
    c.sh.systemd("reload")
    c.sh.systemd("enable", "uwsgi.service")
    # c.sh.systemd("enable", "uwsgi-emperor.service')
    c.sh.systemd("restart", "uwsgi.service")


def setup(c: Context) -> None:
    if not c.app.wsgi or c.app.wsgi.type != WsgiTypes.UWSGI:
        return
    generate(c)
    deploy(c)
    activate(c)
