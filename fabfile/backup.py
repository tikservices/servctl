from typing import Optional
from fabfile.context import Context
from . import db
from datetime import date


def backup(c: Context, name: Optional[str] = None) -> None:
    if not name:
        name = date.today().isoformat()
    # backup psql db
    sql_r = f"/tmp/{c.app.project.name}-{name}.sql.tar"
    sql_l = f"./backups/{c.app.project.name}-{name}.sql.tar"
    cmd_sql = f"pg_dump --dbname={c.app.project.name} \
        -f {sql_r} --format=tar \
      --no-acl --no-owner \
    "
    c.sh.sudo(cmd_sql, user="postgres")
    c.sh.get(sql_r, sql_l)

    # backup upload/
    dir_r = f"/tmp/{c.app.project.name}-{name}.dir.zip"
    dir_l = f"./backups/{c.app.project.name}-{name}.dir.zip"
    cmd_dir = f"bash -c 'cd {c.app.project.www_dir} && zip -9 -r {dir_r} ./upload/'"
    c.sh.sudo(cmd_dir, user="www-data")
    c.sh.get(dir_r, dir_l)


def restore(c: Context, name: str) -> None:
    sql_r = f"/tmp/{c.app.project.name}-{name}.sql.tar"
    sql_l = f"./backups/{c.app.project.name}-{name}.sql.tar"
    cmd_sql = f"""pg_restore {sql_r} --dbname={c.app.project.name} \
      --format=tar \
      --clean --if-exists \
      --exit-on-error --single-transaction \
      --no-acl --no-owner --role={c.app.project.name} \
    """
    c.sh.put(sql_l, sql_r)

    s1 = c.sh.sudo(f"systemctl stop gunicorn@{c.app.project.name}.socket", warn=True)
    s2 = c.sh.sudo(f"systemctl stop gunicorn@{c.app.project.name}.service", warn=True)
    s3 = c.sh.sudo(f"systemctl stop celery@{c.app.project.name}.service", warn=True)
    s4 = c.sh.sudo(f"systemctl stop celerybeat@{c.app.project.name}.service", warn=True)

    db.postgres_enable_superuser(c, True)
    c.sh.sudo(cmd_sql, user="postgres")
    db.postgres_enable_superuser(c, False)

    if c.app.db:
        db.create_psql_db_extensions(c, c.app.db_name, c.app.db.extensions)
        db.set_psql_db_permissions(c, c.app.db_name)

    if s1:
        c.sh.systemd("start", f"gunicorn@{c.app.project.name}.socket")
    if s2:
        c.sh.systemd("start", f"gunicorn@{c.app.project.name}.service")
    if s3:
        c.sh.systemd("start", f"celery@{c.app.project.name}.service")
    if s4:
        c.sh.systemd("start", f"celerybeat@{c.app.project.name}.service")

    dir_r = f"/tmp/{c.app.project.name}-{name}.dir.zip"
    dir_l = f"./backups/{c.app.project.name}-{name}.dir.zip"
    cmd_dir = f"bash -c 'cd {c.app.project.www_dir} && unzip -o {dir_r}'"
    c.sh.put(dir_l, dir_r)
    c.sh.sudo(cmd_dir, user="www-data")
