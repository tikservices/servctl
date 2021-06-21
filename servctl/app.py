from .context.app_generator import create_app
from typing import Optional
from pathlib import Path
from .utils import log
from .context import Config, ContextWithApp
from .commands import register
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
    nginx,
    gunicorn,
    uwsgi,
    backup as backup_m,
)

@register(name="app:init")
def init(config: Config, host: str) -> None:
    app = create_app(config, host)
    app.export(config)
    print("Config exported to:", app.get_app_file_path(config))


@register(name="app:generate")
def generate(ctxt: ContextWithApp) -> None:
    # ctxt = ContextWithApp.from_app_config(config_file, ctxt_)
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
        # django.generate_settings_secrets(ctxt)
        pass
    log("[Dotenv/Generate]")
    dotenv.generate(ctxt)


@register(name="app:deploy")
def deploy(ctxt: ContextWithApp, force_dns: bool = False) -> None:
    # ctxt = ContextWithApp.from_app_config(config_file, ctxt_)
    app = ctxt.app

    log(f"deploying into: {app.project.host}")

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
    # django.sync_settings_secrets(ctxt)
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


@register(name="app:backup")
def backup(ctxt: ContextWithApp, name: Optional[str] = None) -> None:
    backup_m.backup(ctxt, name)


@register(name="app:restore")
def restore(ctxt: ContextWithApp, config_file: Path, name: str) -> None:
    backup_m.restore(ctxt, name)
