from fabfile.context.shell import Shell
from .utils import safe_render_to
import os
from fabric import task
from .context.app import App, ProjectTypes
from .context import Context
import fabric.connection


def generate_settings_secrets(c: Context) -> None:
    secret_file = c.app.local_dir / "django_settings_secret.py"
    t = c.config.dirs.local.template / "django" / "settings_secret.py.jinga2"
    safe_render_to(c, t, secret_file)


def sync_settings_secrets(c: Context) -> None:
    assert c.app.django, "Django Entry not defined on App file"
    if c.app.project.type != ProjectTypes.DJANGO:
        return
    secret_file = c.app.local_dir / "django_settings_secret.py"
    dst = c.app.project.src_dir / c.app.django.project_module / "settings_secret.py"
    c.sh.upload_etc(c.app, secret_file, dst, owner="www-data", mode=0o400)


def createsuperuser(c: Context) -> None:
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


@task
def sync_uwsgi(c):
    # type: (fabric.connection.Connection) -> None
    c.put("./uwsgi", "/etc", use_sudo=True)
    c.sudo("systemctl restart uwsgi")


@task
def sync_supervisor(c):
    # type: (fabric.connection.Connection) -> None
    c.put("./supervisor", "/etc", use_sudo=True)
    c.sudo("supervisorctl update")


@task
def sync_all_settings_secrets(c):
    # type: (fabric.connection.Connection) -> None
    domains = [
        f[:-3]
        for f in os.listdir("./django_settings_secret")
        if os.path.isfile("./django_settings_secret/" + f) and f.endswith(".py")
    ]
    for domain in domains:
        dst = c.run(
            "find /var/www/{}/html -maxdepth 2 -mindepth 2 \
        -name settings_secret.py".format(
                domain
            )
        )
        c.put("./django_settings_secret/{}.py".format(domain), dst, use_sudo=True)
        c.sudo("chown www-data:www-data {}".format(dst))
    c.sudo("systemctl restart uwsgi")


@task
def backup_settings_secrets(c):
    # type: (fabric.connection.Connection) -> None
    out = c.sudo(
        "find /var/www/ -maxdepth 4 -mindepth 4 -type f \
    -name settings_secret.py"
    )
    secrets = out.split()
    for secret in secrets:
        domain = secret.split("/", 4)[3]
        c.get(secret, "./django_settings_secret/{}.py".format(domain))


@task
def shell(c, config_file):
    # type: (fabric.connection.Connection, str) -> None
    app = App.import_from(config_file)
    assert app.django, "Django entry not set on App file"
    cmd = "pipenv run python manage.py shell"
    cmd = Shell._build_cmd(
        cmd,
        env={
            "DJANGO_SETTINGS_MODULE": f"{app.django.project_module}.settings",
            "PYTHONPATH": str(app.project.src_dir),
        },
        cwd=app.project.src_dir,
    )
    c.sudo(cmd, user="www-data")
