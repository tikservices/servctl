from typing import Optional
from .app import App
from .config import Config
import fabric.connection
import fabric.config


__all__ = ('Connection', )


class Connection(fabric.connection.Connection):  # type: ignore

    @classmethod
    def from_host(cls, host: str, config: Optional[Config] = None) -> "Connection":
        conf = config if config else Config.get_instance()
        o_config = conf.dict()
        o_config['connect_kwargs'] = conf.ssh.dict(exclude={'config_path'})
        o_config['user'] = conf.sysadmin.username
        o_config['sudo'] = {
            'password': conf.sysadmin.password,
        }
        o_config['load_ssh_config'] = True
        if conf.ssh.config_path:
            o_config['ssh_config_path'] = str(conf.ssh.config_path.absolute())
        if conf.shell:
            o_config['run'] = conf.shell.dict()
        f_config = fabric.config.Config(overrides=o_config, lazy=False)
        f_config.load_runtime()
        # con.config.load_ssh_config()
        con = cls(host, config=f_config)
        return con

    @classmethod
    def from_app(cls, app: App, config: Optional[Config] = None) -> "Connection":
        return cls.from_host(app.project.host, config)
