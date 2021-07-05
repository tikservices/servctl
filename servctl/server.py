from .commands import register
from .context import Context, ContextWithApp
from . import db


def create_projects_dirs(c: ContextWithApp) -> None:
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
        c.sh.mkdir(c.app.project.www_dir, owner="www-data", mode=0o750)

    c.sh.mkdir(c.app.project.data_dir, owner="www-data", mode=0o750)
    c.sh.ln(c.app.project.data_dir, c.app.project.var_slink, force=True)
    c.sh.chmod(c.app.project.var_slink, mode=0o750)


def exec_deploy(c: ContextWithApp) -> None:
    if c.sh.exists(c.app.project.src_dir / ".deploy"):
        try:
            db.postgres_enable_superuser(c, True)
            c.sh.sudo(
                f"./.deploy {c.app.project.env.value}",
                user="www-data",
                cwd=c.app.project.src_dir,
                env={"HOME": "/var/www"},
            )
        finally:
            db.postgres_enable_superuser(c, False)


def get_server_default_interface(c: Context) -> dict:
    # code based on ansible get_default_interfaces()
    # from ansible module_utils/facts/network/linux.py
    res = c.sh._sudo("ip -4 route get 8.8.8.8")
    out: str = res.stdout
    words = out.splitlines()[0].split()
    interface = {}
    # A valid output starts with the queried address on the first line
    if len(words) > 0 and words[0] == "8.8.8.8":
        for i in range(len(words) - 1):
            if words[i] == 'dev':
                interface['interface'] = words[i + 1]
            elif words[i] == 'src':
                interface['address'] = words[i + 1]
            elif words[i] == 'via' and words[i + 1] != "8.8.8.8":
                interface['gateway'] = words[i + 1]
    return interface


@register(name="server:update")
def update(c: Context) -> None:
    c.sh.sudo("apt-get update")
    c.sh.sudo("apt-get dist-upgrade -y")
    c.sh.sudo("apt-get clean -y")
    c.sh.sudo("apt-get autoremove -y")


@register(name="server:backup-etc")
def backup_etc(c: Context) -> None:
    bck_d = c.config.dirs.local.backups / "etc"

    c.sh.get("/etc/nginx/", bck_d)
    c.sh.get("/etc/uwsgi/", bck_d)
    c.sh.get("/etc/php/7.0/fpm", bck_d / "php-7.0")
    c.sh.get("/etc/supervisor", bck_d)
    c.sh.get("/etc/postgresql", bck_d)
    c.sh.get("/etc/redis", bck_d)
    c.sh.get("/etc/ufw", bck_d, use_sudo=True)
    c.sh.get("/etc/datadog-agent", bck_d)
    c.sh.get("/etc/letsencrypt", bck_d, use_sudo=True)
    c.sh.get("/etc/odoo", bck_d)
    c.sh.get("/etc/mysql", bck_d)
    c.sh.get("/etc/sudoers", bck_d, use_sudo=True)


@register(name="systemd:restart")
def restart_services(c: Context, *services: str) -> None:
    for service in services:
        if service == "nginx":
            c.sh.sudo("nginx -t")
        elif service == "ssh":
            c.sh.sudo("/usr/sbin/sshd -t -f /etc/ssh/sshd_config")
        c.sh.systemd("restart", service)
