from .commands import register
from .utils import safe_render_to
from .context.app import ProjectTypes
from .context import Context, ContextWithApp


def generate_settings_secrets(c: ContextWithApp) -> None:
    assert c.app.django, "App does not have a Django entity"
    if not c.app.django.secret_settings:
        return
    secret_file = c.app.local_dir / "django_settings_secret.py"
    t = c.config.dirs.local.template / "django" / "settings_secret.py.jinga2"
    safe_render_to(c, t, secret_file)


def sync_settings_secrets(c: ContextWithApp) -> None:
    assert c.app.django, "App does not have a Django entity"
    if c.app.project.type != ProjectTypes.DJANGO:
        return
    if not c.app.django.secret_settings:
        return
    secret_file = c.app.local_dir / "django_settings_secret.py"
    dst = c.app.project.src_dir / c.app.django.project_module / "settings_secret.py"
    c.sh.upload_etc(c.app, secret_file, dst, owner="www-data", mode=0o400)


def createsuperuser(c: ContextWithApp) -> None:
    assert c.app.django, "Django Entry not defined on App file"
    assert c.config.django, "Django setting not found on fabric.yaml"
    c.sh.put(
        c.config.dirs.local.template / "django" / "createsuperuser.py",
        "/tmp/django-createsuperuser.py",
    )
    cmd = f"""\
pipenv run python /tmp/django-createsuperuser.py \
  "{c.config.django.superuser.email}" \
  "{c.config.django.superuser.password}" \
  "{c.config.django.superuser.username}" \
"""
    c.sh.sudo(
        cmd,
        env={
            "DJANGO_SETTINGS_MODULE": f"{c.app.django.project_module}.settings",
            "PYTHONPATH": str(c.app.project.src_dir),
        },
        cwd=c.app.project.src_dir,
        warn=True,
        user="www-data",
    )


@register(name="uwsgi:setup")
def setup_uwsgi(ctxt: Context) -> None:
    ctxt.sh.upload("./uwsgi", "/etc")
    ctxt.sh.systemd("restart", "uwsgi")


@register(name="supervisor:setup")
def sync_supervisor(ctxt: Context) -> None:
    ctxt.sh.upload("./supervisor", "/etc")
    ctxt.sh.sudo("supervisorctl update")


@register(name="django:shell")
def shell(ctxt: ContextWithApp) -> None:
    app = ctxt.app
    assert app.django, "Django entry not set on App file"
    ctxt.sh.sudo(
        "pipenv run python manage.py shell",
        user="www-data",
        cwd=app.project.src_dir,
        pty=True,
        env={
            "DJANGO_SETTINGS_MODULE": f"{app.django.project_module}.settings",
            "PYTHONPATH": str(app.project.src_dir),
        },
    )
