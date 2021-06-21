from .context import Context, ContextWithApp
from typing import List, Optional
from .context.app import App, DbTypes
from .commands import register


def create_db_mysql(c: Context, name: str, password: str) -> None:
    assert c.config.db.mysql, "MySQL Config not defined on fabric.yaml"
    # don't create user if secret_settings found or DROP USER IF EXISTS 'user'@'hosthost';
    c.sh.run(
        f"""mysql -hlocalhost -u root -p{c.config.db.mysql.root_password} -S /var/run/mysqld/mysqld.sock \
-e "CREATE USER IF NOT EXISTS '{name}'@'localhost' IDENTIFIED BY '{password}';" \
-e "CREATE DATABASE IF NOT EXISTS {name} CHARACTER SET utf8;" \
-e "GRANT ALL ON {name}.* TO '{name}'@'localhost';" \
-e "FLUSH PRIVILEGES;"
"""
    )


def set_psql_db_permissions(c: Context, name: str) -> None:
    cmds = [
        f"""ALTER DATABASE "{name}" OWNER TO "{name}";""",
        f"""ALTER ROLE "{name}" SET client_encoding TO "utf8";""",
        f"""ALTER ROLE "{name}" SET default_transaction_isolation TO "read committed";""",
        f"""ALTER ROLE "{name}" SET timezone TO "UTC";""",
        f"""GRANT CREATE ON DATABASE "{name}" TO "{name}";""",
        f"""GRANT ALL ON ALL TABLES IN SCHEMA public TO "{name}";""",
        f"""GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO "{name}";""",
        f"""GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO "{name}";""",
    ]
    for cmd in cmds:
        c.sh.sudo(f"psql -c '{cmd}'", user="postgres", pty=True)


def create_db_postgres(c: Context, name: str, password: str) -> None:
    cmd1 = f"""psql -tc "SELECT 1 FROM pg_database WHERE datname = '{name}';" | grep -q 1"""
    if c.sh.sudo(cmd1, user="postgres", warn=True):
        print("Database already created! returning!")
        return
    cmds = [
        f"""CREATE ROLE "{name}" WITH PASSWORD '"'{password}'"' NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT LOGIN;""",
        f"""CREATE DATABASE "{name}" OWNER "{name}";""",
    ]
    for cmd in cmds:
        c.sh.sudo(f"psql -c '{cmd}'", user="postgres", pty=True)
    set_psql_db_permissions(c, name)


def create_psql_db_extensions(
    c: Context, name: str, extensions: Optional[List[str]]
) -> None:
    if not extensions:
        return
    for ext in extensions:
        c.sh.sudo(
            f"psql {name} -c 'CREATE EXTENSION IF NOT EXISTS {ext};'",
            user="postgres",
            pty=True,
        )


def postgres_enable_superuser(c: ContextWithApp, enable: bool) -> None:
    if not c.app.db or c.app.db.driver != DbTypes.POSTGRES:
        return
    opt = "SUPERUSER" if enable else "NOSUPERUSER"
    cmd = f"""ALTER ROLE "{c.app.db_name}" WITH {opt};"""
    c.sh.sudo(f"psql -c '{cmd}'", user="postgres", pty=True)


def setup(c: ContextWithApp) -> None:
    assert c.app.db, "DB entry not defined on app file"
    name = c.app.db_name
    password = c.app.db.password
    driver = c.app.db.driver

    if driver == DbTypes.MYSQL:
        create_db_mysql(c, name, password)
    elif driver == DbTypes.POSTGRES:
        create_db_postgres(c, name, password)
        create_psql_db_extensions(c, name, c.app.db.extensions)


@register("db:shell")
def shell(ctxt: Context, app: Optional[App] = None, driver: Optional[str] = None) -> None:
    config = ctxt.config
    if app:
        assert app.db, "DB entry not defined on app file"
        name = app.project.name
        password = app.db.password
        user = name
        driver = app.db.driver
    else:
        name = ""
        user = "root"
        driver = driver if driver else "postgres"
        if driver == "mysql":
            assert config.db.mysql, "MySQL Config not defined on fabric.yaml"
            password = config.db.mysql.root_password
        elif driver == "postgres":
            assert config.db.postgres, "PostgreSQL Config not defined on fabric.yaml"
            password = config.db.postgres.root_password
        else:
            password = ""
    if driver == "mysql":
        ctxt.sh.run(
            """
mysql -hlocalhost -u {user} -p{password} -S /var/run/mysqld/mysqld.sock {name}
""".format(
                name=name, user=user, password=password
            )
        )
    elif driver == "postgres":
        ctxt.sh.sudo(
            f"psql -U{user} {name}",
            user="postgres", pty=True,
            env={
                "PGPASSWORD": password,
            },
        )
