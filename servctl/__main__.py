#!/usr/bin/env python3

from .commands import CommandsManager


# config_p = Path("config.yaml")
# config = Config.import_from(config_p)
#
# con = Connection.from_host(host, config)
# ctxt = Context.from_fabric_connection(con, config)

CommandsManager.run()
