#!/usr/bin/env python3

from pathlib import Path
from typing_extensions import runtime
from fabfile.context.config import Config
import fabric.connection
import fabric.config
import sys
from fabfile import deploy, init, generate

host = sys.argv[1]
cmd = sys.argv[2]
try:
    app = sys.argv[3]
except:
    app = None

config_p = Path("config.yaml")
config = Config.import_from(config_p)

def create_connection(config: Config, host: str) -> fabric.connection.Connection:
    o_config = config.dict()
    o_config['connect_kwargs'] = config.ssh.dict(exclude={'config_path'})
    o_config['user'] = config.sysadmin.username
    o_config['sudo'] = {
        'password': config.sysadmin.password,
    }
    o_config['load_ssh_config'] = True
    if config.ssh.config_path:
        o_config['ssh_config_path'] = str(config.ssh.config_path.absolute())
    if config.shell:
        o_config['run'] = config.shell.dict()
    f_config = fabric.config.Config(overrides=o_config, lazy=False)
    f_config.load_runtime()
    # con.config.load_ssh_config()
    con = fabric.connection.Connection(host, config=f_config)
    return con

con = create_connection(config, host)

if cmd == 'deploy':
    assert app
    deploy(con, app)
elif cmd == 'init':
    init(con)
elif cmd == 'generate':
    assert app
    generate(con, app)
