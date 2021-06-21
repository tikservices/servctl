from servctl.commands import register
from .context import Context, ContextWithApp
from .utils import safe_render_to
from .context.app import WsgiTypes


def generate(c: ContextWithApp, template: str = "gunicorn") -> None:
    if not c.app.wsgi or c.app.wsgi.type != WsgiTypes.GUNICORN:
        return
    app_file = c.app.local_dir / "gunicorn.conf"
    t = c.config.dirs.local.template / "gunicorn" / f"{template}.jinja2"
    safe_render_to(c, t, app_file)


def deploy(c: ContextWithApp) -> None:
    if not c.app.wsgi or c.app.wsgi.type != WsgiTypes.GUNICORN:
        return
    app_file = c.app.local_dir / "gunicorn.conf"
    c.sh.upload_etc(c.app, app_file, f"/etc/gunicorn/{c.app.project.name}.conf")
    activate(c)


def activate(c: ContextWithApp) -> None:
    if not c.app.wsgi or c.app.wsgi.type != WsgiTypes.GUNICORN:
        return
    c.sh.systemd("reload")
    c.sh.systemd("enable", f"gunicorn@{c.app.project.name}.socket")
    c.sh.systemd("restart", f"gunicorn@{c.app.project.name}.service")


def setup(c: ContextWithApp) -> None:
    if not c.app.wsgi or c.app.wsgi.type != WsgiTypes.GUNICORN:
        return
    generate(c)
    deploy(c)
    activate(c)


@register(name="gunicorn:setup")
def sync_services(c: Context) -> None:
    g_dir = c.config.dirs.local.template / "gunicorn"

    c.sh.mkdir("/etc/gunicorn", owner="root", mode=0o755)
    c.sh.upload(g_dir / "gunicorn@.service", "/etc/systemd/system")
    c.sh.upload(g_dir / "gunicorn@.socket", "/etc/systemd/system")
    c.sh.upload(g_dir / "gunicorn.service", "/etc/systemd/system")
    c.sh.upload(g_dir / "gunicorn.tmpfiles", "/etc/tmpfiles.d/gunicorn.conf")

    c.sh.systemd("reload")
