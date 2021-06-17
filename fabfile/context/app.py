from typing import List, Optional, Literal, Union
from .config import Config
from . import config as conf_m
from pydantic import BaseModel, AnyUrl

# from pydantic.dataclasses import dataclass
from pathlib import Path
import yaml
import json
from giturlparse import parse as giturlparse
from enum import Enum


DEFAULT_BRANCH = "master"


class Repo(BaseModel):
    branch: str = DEFAULT_BRANCH
    url: str  # AnyUrl
    # name: str
    # path: str
    private: bool = True

    @property
    def owner(self) -> str:
        return str(giturlparse(self.url).owner)

    @property
    def name(self) -> str:
        return str(giturlparse(self.url).name)

    @property
    def path(self) -> str:
        return f"{self.owner}/{self.name}"

    @property
    def host(self) -> str:
        return str(giturlparse(self.url).host)

    @staticmethod
    def validate_url(url: str) -> bool:
        return bool(giturlparse(url).valid)

    @property
    def deploy_key(self) -> Optional[Path]:
        if not self.private:
            return None
        return Path("/var/www/.ssh") / self.host / self.owner / self.name / "id_ed25519"


Domains = List[str]


class DbTypes(str, Enum):
    POSTGRES = "postgres"
    MYSQL = "mysql"
    SQLITE = "sqlite"


DEFAULT_DB_TYPE = DbTypes.POSTGRES


class DB(BaseModel):
    driver: DbTypes = DEFAULT_DB_TYPE
    name: Optional[str]
    password: str
    extensions: Optional[List[str]]


DEFAULT_DJANGO_ADMIN_PATH = "admin"


class Django(BaseModel):
    secret: str
    admin_path: str = DEFAULT_DJANGO_ADMIN_PATH
    project_module: str


class QueueTypes(str, Enum):
    CELERY = "celery"


class WsgiTypes(str, Enum):
    UWSGI = "uwsgi"
    GUNICORN = "gunicorn"


class WSGI(BaseModel):
    type: WsgiTypes
    app_path: str


class Envs(str, Enum):
    PRODUCTION = "production"
    TEST = "test"


class ProjectTypes(str, Enum):
    DJANGO = "django"
    FLASK = "flask"
    STATIC = "static"


DEFAULT_DOTENV_PATH = ".env"


class Project(BaseModel):
    env: Envs = Envs.PRODUCTION
    host: str
    type: ProjectTypes
    name: str
    dir: Optional[Path]
    dotenv_path: str = DEFAULT_DOTENV_PATH
    public_dir: Optional[Path]

    def get_public_dir(self) -> Optional[Path]:
        if self.public_dir and self.public_dir.is_absolute():
            return self.public_dir.resolve()
        elif self.public_dir:  # relative to absolute
            return (Path("/") / self.public_dir).resolve()
        elif self.type == ProjectTypes.STATIC:
            return Path("/")
        return None

    @property
    def DEBUG(self) -> bool:
        return self.env != Envs.PRODUCTION

    @property
    def app_dir(self) -> Path:
        if self.dir:
            return self.dir
        elif conf_m.current_config:
            return conf_m.current_config.dirs.server.apps / self.name
        else:
            return conf_m.DEFAULT_SERVER_APPS_DIR / self.name

    @property
    def src_dir(self) -> Path:
        return self.app_dir / "src/"

    @property
    def tmp_dir(self) -> Path:
        return self.app_dir / "tmp/"

    @property
    def www_dir(self) -> Path:
        return self.app_dir / "www/"

    @property
    def etc_dir(self) -> Path:
        return self.app_dir / "etc/"

    @property
    def data_dir(self) -> Path:
        if conf_m.current_config:
            return conf_m.current_config.dirs.server.apps_data / self.name
        else:
            return conf_m.DEFAULT_SERVER_APPS_DATA_DIR / self.name

    @property
    def var_slink(self) -> Path:
        return self.app_dir / "var/"


# emails:
#   username: forward@email1
#   username:
#     - forward@email1
#     - forward@email2
Emails = dict[str, Union[str, List[str]]]


class App(BaseModel):
    __slots__ = ("_local_dir",)
    project: Project
    repo: Repo
    domains: Domains
    db: Union[DB, Literal[False]]
    django: Optional[Django]
    queue: Union[QueueTypes, None, Literal[False]]
    wsgi: Optional[WSGI]
    emails: Optional[Emails]

    @property
    def domain(self) -> str:
        return self.domains[0]

    @property
    def db_name(self) -> str:
        return self.db.name if self.db and self.db.name else self.project.name

    @property
    def local_dir(self) -> Path:
        if hasattr(self, "_local_dir"):
            return Path(getattr(self, "_local_dir"))
        else:
            raise Exception("App local dir not defined")

    def set_local_dir(self, p: Union[str, Path]) -> None:
        object.__setattr__(self, "_local_dir", Path(p))

    @classmethod
    def import_from(cls, file_p: Union[str, Path]) -> "App":
        global current_app
        app_f = Path(file_p)
        with app_f.open() as f:
            _app = yaml.safe_load(f.read())
            app = App.parse_obj(_app)
            app.set_local_dir(app_f.parent)
            current_app = app
            return app

    def get_app_file_path(self, conf: Optional[Config] = None) -> Path:
        if not conf and conf_m.current_config:
            conf = conf_m.current_config
        if hasattr(self, "_local_dir"):
            app_dir = self.local_dir
        elif conf:
            apps_dir = conf.dirs.local.apps
            app_dir = Path(apps_dir) / self.project.name
        else:
            apps_dir = Path("apps")
            app_dir = apps_dir / self.project.name
        app_dir.mkdir(parents=True, exist_ok=True)
        app_f = app_dir / "app.yaml"
        return app_f

    def export(self, conf: Optional[Config] = None) -> None:
        if not conf and conf_m.current_config:
            conf = conf_m.current_config
        _app = json.loads(self.json(exclude_unset=True, exclude_none=True))
        print(yaml.safe_dump(_app, default_flow_style=False))
        app_file = self.get_app_file_path(conf)
        with app_file.open("w") as f:
            yaml.safe_dump(_app, f, default_flow_style=False)


current_app: Optional[App] = None
