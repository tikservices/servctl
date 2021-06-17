from typing import Any, Optional
from .config import Config
from invocations.console import confirm
import re
from .app import App, ProjectTypes, DbTypes, DB, QueueTypes, WsgiTypes
from pathlib import Path
from ..utils import gen_random_token
from giturlparse import parse as giturlparse


class AttributeDict(dict):
    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError:
            # to conform with __getattr__ spec
            raise AttributeError(key)

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value


def __init__conf() -> AttributeDict:
    conf = AttributeDict()
    conf.project = AttributeDict()
    conf.repo = AttributeDict()
    conf.domains = []
    conf.db = False
    conf.django = None
    conf.queque = False
    conf.wsgi = None
    conf.emails = None
    return conf


def prompt(
    text: str, default: Optional[str] = None, validate: Optional[str] = None, values: Optional[list[str]] = None
) -> str:
    res = None
    values_txt = ""
    if values:
        validate = "^" + "|".join(values) + "$"
        values_txt = "|".join(values)
    while not res:
        res = input(f"{text} ({values_txt}) [{default if default is not None else ''}] ")
        res = res.strip()
        if not res and default:
            res = default
        if validate and re.findall(validate, res):
            return res
        elif validate and not re.findall(validate, res):
            res = None
    return res


def create_app(config: Config, host: Optional[str] = None) -> App:
    app = __init__conf()
    if host:
        app.project.host = host
    else:
        app.project.host = prompt("Host server name")
    app.project.name = prompt("Project name")
    app.project.type = ProjectTypes(
        prompt(
            "Project name",
            values=[e.value for e in ProjectTypes],
            default=ProjectTypes.DJANGO.value,
        )
    )
    repo_url = f"git@github.com:{config.github.username}/{app.project.name}"
    app.repo.url = prompt("Repo URL", default=repo_url)
    app.repo.branch = prompt("Repo branch name", default="master")
    app.domains.append(
        prompt("Deploy domain", default="{}.tik.website".format(app.project.name))
    )

    if app.project.type == ProjectTypes.DJANGO:
        app.django = AttributeDict()
        app.django.project_module = prompt("Django project name", default="project")
        app.wsgi = AttributeDict()
        app.wsgi.app_path = f"{app.django.project_module}.wsgi:application"
        app.wsgi.type = WsgiTypes.GUNICORN
    if app.project.type == ProjectTypes.FLASK:
        app.wsgi = AttributeDict()
        app.wsgi.app_path = prompt("WSGI app module path", default="wsgi:app")
        app.wsgi.type = WsgiTypes.GUNICORN
    if app.project.type in (ProjectTypes.DJANGO, ProjectTypes.FLASK):
        app.db = AttributeDict()
        app.db.driver = DbTypes(
            prompt(
                "Database driver",
                values=[e.value for e in DbTypes],
                default=DbTypes.POSTGRES.value,
            )
        )
    if app.project.type in (ProjectTypes.DJANGO, ProjectTypes.FLASK):
        queue_vals = [e.value for e in QueueTypes]
        queue_vals.append('')
        app_queue = prompt(
            "Task Queue driver", values=queue_vals, default=""
        )
        if len(app_queue):
            app.queue = QueueTypes(app_queue)

    if app.project.type == ProjectTypes.STATIC:
        app.project.public_dir = Path(prompt("Public dir", default="/", validate=r"^\/.*$"))

    app.repo.private = confirm("Repo private and requires generating deployment key")
    gen_tokens(app)

    _app = App.parse_obj(app)
    return _app


def gen_tokens(app: AttributeDict) -> None:
    if app.db:
        app.db.password = gen_random_token()
    if app.django:
        app.django.secret = gen_random_token(only_word_chars=False)
        app.django.admin_path = gen_random_token()
