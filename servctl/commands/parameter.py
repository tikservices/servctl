from inspect import Parameter
from typing import Any, Callable, ClassVar, Mapping, Type, Union
from ..context import Context, ContextWithApp, App, Connection, Config
import typing


def is_required(arg: Parameter) -> bool:
    if arg.default is not Parameter.empty:
        return False
    elif typing.get_origin(arg.annotation) is Union and type(None) in typing.get_args(
        arg.annotation
    ):
        return False
    return True


def nargs(arg: Parameter) -> Union[int, str]:
    if arg.kind == arg.POSITIONAL_ONLY:  # arg /
        return 1
    elif arg.kind == arg.POSITIONAL_OR_KEYWORD:  # arg
        return 1 if is_required(arg) else "?"
    elif arg.kind == arg.VAR_POSITIONAL:  # *args
        return "*"
    elif arg.kind == arg.KEYWORD_ONLY:  # *args, arg1, arg2
        return 1
    elif arg.kind == arg.VAR_KEYWORD:  # **kwargs
        return "*"
    else:
        return 1


def action(arg: Parameter) -> str:
    if arg.kind == arg.VAR_POSITIONAL:
        return "append"
    elif arg.annotation == bool:
        return "store_true"
    else:
        return "store"


def name(arg: Parameter) -> str:
    _type = type_of(arg)
    if issubclass(_type, ContextWithApp):
        return "app"
    elif issubclass(_type, App):
        return "app"
    elif issubclass(_type, Context):
        return "host"
    elif issubclass(_type, Connection):
        return "host"
    elif issubclass(_type, Config):
        return "config"
    else:
        return arg.name.strip("_").replace('_', '-')


def type_of(arg: Parameter) -> Any:
    _type = arg.annotation
    if typing.get_origin(_type) is Union:
        _types = typing.get_args(_type)
        _type = next(
            (_type for _type in _types if _type is not type(None)),
            type(None),
        )
    return _type


def _strtobool(v: str) -> bool:
    if v.lower() in ("t", "true", "y", "yes", "on", "1"):
        return True
    elif v.lower() in ("f", "false", "n", "no", "off", "0"):
        return False
    else:
        raise ValueError(f"can not convert value {v:r} to bool")


PARSERS: Mapping[Type[Any], Callable[[Any], Any]] = {
        Config: Config.import_from,
        App: App.import_from,
        Context: Context.from_host,
        ContextWithApp: ContextWithApp.from_app_config,
        Connection: Connection.from_host,
        bool: bool,  # _strtobool,
}


def parser(arg: Parameter) -> Callable[[Any], Any]:
    _type = type_of(arg)
    return PARSERS.get(_type, _type)
