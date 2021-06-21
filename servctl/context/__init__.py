from pathlib import Path
from .connection import Connection
from .shell import Shell
from typing import Optional, Union
from .config import Config
from .app import App
import fabric.connection
from dataclasses import dataclass


__all__ = ("App", "Config", "Shell", "Context", "ContextWithApp", "Connection", "current_context")


@dataclass
class Context:
    app: Optional[App]
    config: Config
    con: fabric.connection.Connection
    sh: Shell
    offline: bool = False

    @classmethod
    def from_fabric_connection(
        cls, con: fabric.connection.Connection, config: Optional[Config] = None, offline: Optional[bool] = None
    ) -> "Context":
        global current_context
        if not config:
            config = Config.get_instance()
        current_context = cls(app=None, config=config, con=con, sh=Shell(con))
        if offline is not None:
            current_context.offline = offline
        return current_context

    @classmethod
    def from_host(cls, host: str, config: Optional[Config] = None) -> "Context":
        return cls.from_fabric_connection(con=Connection.from_host(host), config=config)


@dataclass
class ContextWithApp(Context):
    app: App

    @classmethod
    def from_app(cls, app: App, ctxt: Optional[Context] = None) -> "ContextWithApp":
        if not ctxt:
            ctxt = Context.from_host(app.project.host)
        ctxt_app = cls(app=app, config=ctxt.config, con=ctxt.con, sh=ctxt.sh, offline=ctxt.offline)
        return ctxt_app

    @classmethod
    def from_app_config(cls, config_f: Union[str, Path], ctxt: Optional[Context] = None) -> "ContextWithApp":
        app = App.import_from(config_f)
        return cls.from_app(app, ctxt)


current_context: Optional[Context] = None
