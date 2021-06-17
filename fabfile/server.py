from .context import Context
import os
from fabric import task
import fabric.connection
from . import db


def create_projects_dirs(c: Context) -> None:
    c.sh.mkdir(c.app.project.app_dir, owner="www-data", mode=0o550)
    c.sh.mkdir(c.app.project.src_dir, owner="www-data", mode=0o750)
    c.sh.mkdir(c.app.project.tmp_dir, owner="www-data", mode=0o750)
    c.sh.mkdir(c.app.project.etc_dir, owner="www-data", mode=0o550)

    public_dir = c.app.project.get_public_dir()
    if public_dir:
        pub = c.app.project.src_dir / public_dir.relative_to("/")
        c.sh.rm(c.app.project.www_dir)
        c.sh.ln(pub, c.app.project.www_dir, force=True)
    else:
        c.sh.mkdir(c.app.project.www_dir, owner="www-data", mode=0o550)

    c.sh.mkdir(c.app.project.data_dir, owner="www-data", mode=0o750)
    c.sh.ln(c.app.project.data_dir, c.app.project.var_slink, force=True)
    c.sh.chmod(c.app.project.var_slink, mode=0o750)


def exec_deploy(c: Context) -> None:
    if c.sh.exists(c.app.project.src_dir / ".deploy"):
        try:
            db.postgres_enable_superuser(c, True)
            c.sh.sudo(
                f"./.deploy {c.app.project.env.name}",
                user="www-data",
                cwd=c.app.project.src_dir,
                env={"HOME": "/var/www"},
            )
        finally:
            db.postgres_enable_superuser(c, False)


@task
def update(c):
    # type: (fabric.connection.Connection) -> None
    c.sudo("apt-get update")
    c.sudo("apt-get dist-upgrade -y")
    c.sudo("apt-get clean -y")
    c.sudo("apt-get autoremove -y")


@task
def backup_etc(c):
    # type: (fabric.connection.Connection) -> None
    for f in os.listdir("./nginx"):
        c.get(f"/etc/nginx/{f}", "./nginx/")
    for f in os.listdir("./uwsgi"):
        c.get(f"/etc/uwsgi/{f}", "./uwsgi/{f}")
    for f in os.listdir("./php-7.0/fpm"):
        c.get("/etc/php/7.0/fpm/" + f, "./php-7.0/fpm")
    c.get("/etc/supervisor", ".")
    c.get("/etc/postgresql", ".")
    c.get("/etc/redis", ".")
    c.get("/etc/ufw", ".", use_sudo=True)
    c.get("/etc/datadog-agent", ".")
    c.get("/etc/letsencrypt", ".", use_sudo=True)
    c.get("/etc/odoo", ".")
    c.get("/etc/mysql", ".")
    c.get("/etc/sudoers", ".", use_sudo=True)


@task
def restart_services(c, *services):
    # type: (fabric.connection.Connection, str) -> None
    for service in services:
        if service == "nginx":
            c.sudo("nginx -t")
        c.sudo("systemctl restart " + service)
