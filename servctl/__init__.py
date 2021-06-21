import os
from pathlib import Path
from .commands import register
from . import (
    app, mail, utils
)


BASE_DIR = Path(__file__).absolute().parents[2]


@register(name="gentoken")
def gen_token(length: int = 50) -> None:
    print(utils.gen_random_token(length=length))
