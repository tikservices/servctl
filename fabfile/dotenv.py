from .utils import safe_render_to
from .context import Context


def generate(c: Context) -> None:
    template = c.app.project.type
    app_file = c.app.local_dir / "dotenv"
    t = c.config.dirs.local.template / "dotenv" / f"{template}.jinja2"
    safe_render_to(c, t, app_file)


def deploy(c: Context) -> None:
    app_file = c.app.local_dir / "dotenv"
    dotenv_dst = c.app.project.dotenv_path
    dst = c.app.project.src_dir / dotenv_dst
    c.sh.upload_etc(c.app, app_file, dst, owner="www-data", mode=0o400)


def setup(c: Context) -> None:
    generate(c)
    deploy(c)
