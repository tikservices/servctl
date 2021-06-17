from .shell import Shell
from typing import Optional
from .config import Config
from .app import App
from fabric.connection import Connection
from dataclasses import dataclass


__all__ = ("App", "Config", "Context", "current_context")


@dataclass
class Context:
    app: App
    config: Config
    con: Connection
    sh: Shell
    offline: bool = False

    @classmethod
    def from_app_config(
        cls, c: Connection, config_f: str, offline: Optional[bool] = None
    ) -> "Context":
        global current_context
        app = App.import_from(config_f)
        config = Config.config_from_conection(c)
        current_context = cls(app=app, config=config, con=c, sh=Shell(c))
        if offline is not None:
            current_context.offline = offline
        return current_context


current_context: Optional[Context] = None
