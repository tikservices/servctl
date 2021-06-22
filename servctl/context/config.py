from typing import Optional, Union, cast
from pydantic import BaseModel

# from pydantic.dataclasses import dataclass
from pathlib import Path
import fabric.config
import fabric.connection
import yaml


class GitHub(BaseModel):
    access_token: str
    webhook_secret: str
    username: str


class MySQL(BaseModel):
    root_password: str


class Postgres(BaseModel):
    root_password: str


class DB(BaseModel):
    mysql: Optional[MySQL]
    postgres: Optional[Postgres]


class OVH(BaseModel):
    endpoint: str = "ovh-eu"
    application_key: str
    application_secret: str
    consumer_key: str


class DataDog(BaseModel):
    api_key: str


class LocalDirs(BaseModel):
    apps: Path
    template: Path
    backups: Path


DEFAULT_SERVER_APPS_DIR = Path("/apps/")
DEFAULT_SERVER_APPS_DATA_DIR = Path("/data/")


class ServerDirs(BaseModel):
    apps: Path = DEFAULT_SERVER_APPS_DIR
    apps_data: Path = DEFAULT_SERVER_APPS_DATA_DIR


class Dirs(BaseModel):
    local: LocalDirs
    server: ServerDirs


class DjangoSuperuser(BaseModel):
    username: str
    email: str
    password: str


class Django(BaseModel):
    superuser: DjangoSuperuser


class Webmaster(BaseModel):
    full_name: str
    email: str


class Sysadmin(BaseModel):
    full_name: str
    username: str
    password: Optional[str]
    email: str


class Ssh(BaseModel):
    passphrase: Optional[str] = None
    password: Optional[str] = None
    # key_filename: list[str] = []
    config_path: Optional[Path] = None


class Shell(BaseModel):
    dry: bool = False
    echo: bool = False
    echo_format: Optional[str] = None
    pty: bool = False
    warn: bool = False
    shell: str = "/bin/bash"
    env: Optional[dict[str, str]] = None


class Config(BaseModel):
    dirs: Dirs
    github: GitHub
    django: Optional[Django]
    webmaster: Webmaster
    ovh: OVH
    db: DB
    sysadmin: Sysadmin
    datadog: DataDog
    ssh: Ssh
    shell: Optional[Shell]

    @classmethod
    def import_from(cls, file_p: Union[str, Path] = 'config.yaml') -> "Config":
        global current_config
        path = Path(file_p)
        with path.open() as f:
            _data = yaml.safe_load(f.read())
            config = cls.parse_obj(_data)
            current_config = config
            return config

    @classmethod
    def from_fabric_config(cls, c: fabric.config.Config) -> "Config":
        global current_config
        config = cls.parse_obj(c)
        current_config = config
        return config

    @classmethod
    def from_fabric_connection(cls, c: fabric.connection.Connection) -> "Config":
        return cls.from_fabric_config(cast(fabric.config.Config, c.config))

    @classmethod
    def get_instance(cls) -> "Config":
        if current_config:
            return current_config
        return cls.import_from()


current_config: Optional[Config] = None
