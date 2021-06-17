from .context import Context
from .utils import render, safe_render_to
from fabric import task
import fabric.connection


def generate(c: Context, force: bool = False) -> None:
    site_file = c.app.local_dir / "nginx.conf"
    t = (
        c.config.dirs.local.template
        / "nginx"
        / "sites-available"
        / f"{c.app.project.type}.jinja2"
    )
    safe_render_to(c, t, site_file, with_certificates=True)


def deploy(c: Context) -> None:
    site_file = c.app.local_dir / "nginx.conf"
    c.sh.upload_etc(c.app, site_file, f"/etc/nginx/sites-enabled/{c.app.project.name}", mode=0o440)
    restart(c)


def upload_tmp_nginx_site(c: Context) -> None:
    from tempfile import NamedTemporaryFile

    t = (
        c.config.dirs.local.template
        / "nginx"
        / "sites-available"
        / f"{c.app.project.type}.jinja2"
    )
    dst_f = f"/etc/nginx/sites-enabled/{c.app.project.name}"
    res = render(c, t, with_certificates=False)
    with NamedTemporaryFile("w") as f:
        f.write(res)
        f.flush()
        c.sh.rm(dst_f)
        c.sh.upload(f.name, dst_f, mode=0o740)


def restart(c: Context) -> None:
    c.sh.sudo("nginx -t", warn=False)
    c.sh.systemd("restart", "nginx.service")
