from logging import warning
from jinja2.environment import Template
from .context import Context
import secrets
from pathlib import Path
from typing import Any, Union
from fabric.connection import Connection


def gen_random_token(only_word_chars: bool = True, length: int = 50) -> str:
    chars = "A-Za-z0-9" if only_word_chars else "A-Za-z0-9!@#$%^&(_=)*+-"
    # token = local('head /dev/urandom | tr -dc "{}" | head -c {}'
    #               .format(chars, length), capture=True)
    token = "".join(secrets.choice(chars) for i in range(length))
    return str(token)


def upload_file(
    c: Connection, local_p: Union[str, Path], remote_p: Union[str, Path]
) -> None:
    file_n = Path(local_p).name
    c.put(str(local_p), f"/tmp/{file_n}")
    c.sudo(f"mv /tmp/{file_n} {remote_p}")


def render(c: Context, t: Path, **kwargs: Any) -> str:
    with Path(t).open() as tmpl:
        template = Template(tmpl.read())
        res = template.render(app=c.app, conf=c.config, **kwargs)
        return res


def render_to(c: Context, t: Path, dst: Path, **kwargs: Any) -> None:
    res = render(c, t, **kwargs)
    with Path(dst).open("w") as f:
        f.write(res)


def safe_render_to(c: Context, t: Path, dst: Path, **kwargs: Any) -> bool:
    if dst.exists():
        warning(f"Ignoring regenerating file '{dst}'! File exists!!")
        return False
    else:
        render_to(c, t, dst, **kwargs)
        return True
