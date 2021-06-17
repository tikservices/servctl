import os
import sys
from typing import Optional
from fabric import task
import fabric.connection
from invoke import Collection
from .context.app_generator import create_app
from .utils import gen_random_token
from .context import Context, Config
from .context.app import ProjectTypes
from . import (
    db,
    django,
    server,
    ssl,
    dns,
    git,
    celery,
    webmaster,
    dotenv,
    mail,
    nginx,
    gunicorn,
    uwsgi,
    backup as backup_m,
)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def log(msg: str) -> None:
    print(msg, end="\n", flush=True, file=sys.stderr)


@task
def sync_odoo(c):
    # type: (fabric.connection.Connection) -> None
    c.put("./odoo", "/etc", use_sudo=True)
    server.restart_services(c, "odoo")


@task
def init(c):
    # type: (fabric.connection.Connection) -> None
    conf = Config.config_from_conection(c)
    app = create_app(conf, c.host)
    app.export(conf)
    generate(c, str(app.get_app_file_path()))


@task
def generate(c, config_file):
    # type: (fabric.connection.Connection, str) -> None
    ctxt = Context.from_app_config(c, config_file, offline=True)
    app = ctxt.app

    log("[Server/Generate]")
    nginx.generate(ctxt)
    if app.project.type != ProjectTypes.STATIC:
        log("[TaskQueue/Generate]")
        celery.generate(ctxt)
    if app.project.type in (ProjectTypes.DJANGO, ProjectTypes.FLASK):
        log("[Gunicorn/Generate]")
        gunicorn.generate(ctxt)
        log("[UWSGI/Generate]")
        uwsgi.generate(ctxt, template=app.project.type.name)
    if app.project.type == ProjectTypes.DJANGO:
        # log("[Django/Generate_Settings_Secrets]")
        # django.generate_settings_secrets(c)
        pass
    log("[Dotenv/Generate]")
    dotenv.generate(ctxt)


@task(default=True)
def deploy(c, config_file, force_dns=False):
    # type: (fabric.connection.Connection, str, bool) -> None
    log(f"deploying into: {c.host}")
    ctxt = Context.from_app_config(c, config_file)
    app = ctxt.app

    log("[Server/Create_Project_Dirs]")
    server.create_projects_dirs(ctxt)
    log("[Git/GEN_Deploy_Key]")
    git.gen_deploy_key(ctxt)
    log("[Git/Register_Deploy_Key]")
    git.register_deploy_key(ctxt)
    if app.db:
        log("[DB/Setup]")
        db.setup(ctxt)
    log("[Git/Clone]")
    git.clone(ctxt)
    log("[Dotenv/Sync]")
    dotenv.deploy(ctxt)
    # log("[Django/Sync_Settings_Secrets]")
    # django.sync_settings_secrets(c)
    log("[DNS/Register_Domains]")
    domains = dns.get_domains(ctxt)
    dns.register_domains(ctxt, force_dns, *domains)
    nginx.upload_tmp_nginx_site(ctxt)
    nginx.restart(ctxt)
    ssl.generate_for_domains(ctxt, *domains)
    nginx.deploy(ctxt)
    log("[Server/Exec_Deploy]")
    server.exec_deploy(ctxt)
    if app.project.type in (ProjectTypes.DJANGO, ProjectTypes.FLASK):
        log("[UWSGI/Deploy]")
        uwsgi.deploy(ctxt)
        log("[Gunicorn/Deploy]")
        gunicorn.deploy(ctxt)
        log("[TaskQueue/Deploy]")
        celery.deploy(ctxt)
    if app.project.type == ProjectTypes.DJANGO:
        log("[Django/CreateSuperUser]")
        django.createsuperuser(ctxt)
    log("[Git/CreatePushWebhook]")
    git.create_push_webhook(ctxt)
    # TODO: register webhook to github_update.php or deploy script?
    # TODO: generate social media tokens
    # TODO: create superuser
    # log("[Webmaster/Ping_Sitemap]")
    # webmaster.ping_sitemap(ctxt)


@task()
def backup(c, config_file, name=None):
    # type: (fabric.connection.Connection, str, Optional[str]) -> None
    ctxt = Context.from_app_config(c, config_file)
    backup_m.backup(ctxt, name)


@task()
def restore(c, config_file, name):
    # type: (fabric.connection.Connection, str, str) -> None
    ctxt = Context.from_app_config(c, config_file)
    backup_m.restore(ctxt, name)


@task
def gen_token(c, length=50):
    # type: (fabric.connection.Connection, int) -> None
    print(gen_random_token(length=length))


@task
def email_alias(c):
    # type: (fabric.connection.Connection) -> None
    mail.email_alias(c)


ns = Collection(
    deploy,
    init,
    generate,
    backup,
    restore,
    sync_odoo,
    gen_token,
    db,
    django,
    server,
    ssl,
    dns,
    git,
    celery,
    webmaster,
    dotenv,
    mail,
    email_alias,
    gunicorn,
    uwsgi,
)
