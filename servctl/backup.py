from servctl.context.app import DbTypes, ProjectTypes
from typing import Optional
from .context import ContextWithApp
from . import db
from datetime import date


def backup_pgsql(c: ContextWithApp, name: str) -> None:
    sql_r = f"/tmp/{c.app.project.name}-{name}.sql.tar"
    sql_l = f"./backups/{c.app.project.name}-{name}.sql.tar"
    cmd_sql = f"pg_dump --dbname={c.app.db_name} \
        -f {sql_r} --format=tar \
      --no-acl --no-owner \
    "
    c.sh.sudo(cmd_sql, user="postgres")
    c.sh.get(sql_r, sql_l)


def backup_mysql(c: ContextWithApp, name: str) -> None:
    sql_l = f'./backups/{c.app.project.name}-{name}.sql'
    sql_r = f'/tmp/{c.app.project.name}-{name}.sql'
    assert c.config.db.mysql, "MySQL config not defined on config.yaml"
    cmd_sql = f"""mysqldump -hlocalhost -u root -p{c.config.db.mysql.root_password} -S /var/run/mysqld/mysqld.sock \
    --no-create-db --opt --compress \
    --databases {c.app.db_name} --result-file={sql_r} \
    """

    c.sh.run(cmd_sql)
    c.sh.get(sql_r, sql_l)


def backup_django(c: ContextWithApp, name: str) -> None:
    # backup upload/
    dir_r = f"/tmp/{c.app.project.name}-{name}.dir.zip"
    dir_l = f"./backups/{c.app.project.name}-{name}.dir.zip"
    cmd_dir = f"bash -c 'cd {c.app.project.var_dir} && zip -9 -r {dir_r} ./upload/'"
    c.sh.sudo(cmd_dir, user="www-data")
    c.sh.get(dir_r, dir_l)


def backup(c: ContextWithApp, name: Optional[str] = None) -> None:
    if not name:
        name = date.today().isoformat()
    # backup psql db
    if c.app.db and c.app.db.driver == DbTypes.POSTGRES:
        backup_pgsql(c, name)
    elif c.app.db and c.app.db.driver == DbTypes.MYSQL:
        backup_mysql(c, name)
    if c.app.project.type == ProjectTypes.DJANGO:
        backup_django(c, name)


def restore_pgsql(c: ContextWithApp, name: str) -> None:
    sql_r = f"/tmp/{c.app.project.name}-{name}.sql.tar"
    sql_l = f"./backups/{c.app.project.name}-{name}.sql.tar"
    cmd_sql = f"""pg_restore {sql_r} --dbname={c.app.project.name} \
      --format=tar \
      --clean --if-exists \
      --exit-on-error --single-transaction \
      --no-acl --no-owner --role={c.app.project.name} \
    """
    c.sh.put(sql_l, sql_r)

    db.postgres_enable_superuser(c, True)
    c.sh.sudo(cmd_sql, user="postgres")
    db.postgres_enable_superuser(c, False)

    if c.app.db:
        db.create_psql_db_extensions(c, c.app.db_name, c.app.db.extensions)
        db.set_psql_db_permissions(c, c.app.db_name)


def restore_mysql(c: ContextWithApp, name: str) -> None:
    sql_l = f'./backups/{c.app.project.name}-{name}.sql'
    sql_r = f'/tmp/{c.app.project.name}-{name}.sql'
    assert c.config.db.mysql, "MySQL config not defined on config.yaml"
    cmd_sql = f"""mysql -hlocalhost -u root -p{c.config.db.mysql.root_password} -S /var/run/mysqld/mysqld.sock \
    --quick --reconnect --compress \
    --database {c.app.db_name} < {sql_r} \
    """

    # c.sh.put(sql_l, sql_r)
    c.sh.run(cmd_sql, pty=True)


def restore_django(c: ContextWithApp, name: str) -> None:
    dir_r = f"/tmp/{c.app.project.name}-{name}.dir.zip"
    dir_l = f"./backups/{c.app.project.name}-{name}.dir.zip"
    cmd_dir = f"bash -c 'cd {c.app.project.var_dir} && unzip -o {dir_r}'"
    c.sh.put(dir_l, dir_r)
    c.sh.sudo(cmd_dir, user="www-data")


def restore(c: ContextWithApp, name: str) -> None:
    stat = {}
    if c.app.wsgi:
        stat['wsgi_socket'] = c.sh.sudo(f"systemctl stop gunicorn@{c.app.project.name}.socket", warn=True)
        stat['wsgi_service'] = c.sh.sudo(f"systemctl stop gunicorn@{c.app.project.name}.service", warn=True)
    if c.app.queue:
        stat['queque_service'] = c.sh.sudo(f"systemctl stop celery@{c.app.project.name}.service", warn=True)
        stat['queque_schedule_service'] = c.sh.sudo(f"systemctl stop celerybeat@{c.app.project.name}.service", warn=True)

    if c.app.db and c.app.db.driver == DbTypes.POSTGRES:
        restore_pgsql(c, name)
    elif c.app.db and c.app.db.driver == DbTypes.MYSQL:
        restore_mysql(c, name)
    if c.app.project.type == ProjectTypes.DJANGO:
        restore_django(c, name)

    if stat.get('wsgi_socket', False):
        c.sh.systemd("start", f"gunicorn@{c.app.project.name}.socket")
    if stat.get('wsgi_service', False):
        c.sh.systemd("start", f"gunicorn@{c.app.project.name}.service")
    if stat.get('queque_service', False):
        c.sh.systemd("start", f"celery@{c.app.project.name}.service")
    if stat.get('queque_schedule_service', False):
        c.sh.systemd("start", f"celerybeat@{c.app.project.name}.service")
