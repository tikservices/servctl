from .context import Context, Config
from .utils import safe_render_to, upload_file
from fabric import task
import fabric.connection
from .context.app import WsgiTypes


def generate(c: Context, template: str = "gunicorn") -> None:
    if not c.app.wsgi or c.app.wsgi.type != WsgiTypes.GUNICORN:
        return
    app_file = c.app.local_dir / "gunicorn.conf"
    t = c.config.dirs.local.template / "gunicorn" / f"{template}.jinja2"
    safe_render_to(c, t, app_file)


def deploy(c: Context) -> None:
    if not c.app.wsgi or c.app.wsgi.type != WsgiTypes.GUNICORN:
        return
    app_file = c.app.local_dir / "gunicorn.conf"
    c.sh.upload_etc(c.app, app_file, f"/etc/gunicorn/{c.app.project.name}.conf")
    activate(c)


def activate(c: Context) -> None:
    if not c.app.wsgi or c.app.wsgi.type != WsgiTypes.GUNICORN:
        return
    c.sh.systemd("reload")
    c.sh.systemd("enable", f"gunicorn@{c.app.project.name}.socket")
    c.sh.systemd("restart", f"gunicorn@{c.app.project.name}.service")


def setup(c: Context) -> None:
    if not c.app.wsgi or c.app.wsgi.type != WsgiTypes.GUNICORN:
        return
    generate(c)
    deploy(c)
    activate(c)


@task
def sync(c):
    # type: (fabric.connection.Connection) -> None
    # FIXME c.put('./gunicorn', '/etc', use_sudo=True)
    c.sudo("systemctl daemon-reload")


@task
def sync_services(c):
    # type: (fabric.connection.Connection) -> None
    config = Config.config_from_conection(c)
    g_dir = config.dirs.local.template / "gunicorn"

    c.sudo("mkdir -p /etc/gunicorn")
    upload_file(c, g_dir / "gunicorn@.service", "/etc/systemd/system")
    upload_file(c, g_dir / "gunicorn@.socket", "/etc/systemd/system")
    upload_file(c, g_dir / "gunicorn.service", "/etc/systemd/system")
    upload_file(c, g_dir / "gunicorn.tmpfiles", "/etc/tmpfiles.d/gunicorn.conf")

    c.sudo("systemctl daemon-reload")
