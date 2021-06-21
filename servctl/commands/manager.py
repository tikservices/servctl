from ..context import Context, ContextWithApp, Config, Connection, App
from typing import Any, Callable, Optional, Type, TypeVar, Union
import inspect
import argparse
from . import parameter


F = TypeVar('F', bound=Callable[..., None])

class Command:
    def __init__(self, name: str, func: F):
        self.name = name
        self.func = func

    @property
    def help(self) -> Optional[str]:
        return self.func.__doc__

    def add_argument(
        self, args: argparse.ArgumentParser, arg: inspect.Parameter
    ) -> None:

        nargs = parameter.nargs(arg)
        action = parameter.action(arg)
        required = parameter.is_required(arg)
        parser = parameter.parser(arg)
        name = parameter.name(arg)
        default = arg.default
        dest = arg.name

        # print(f"command {self.name} arg {name}")

        if action in ("store_true", "store_false"):
            args.add_argument(f"--{name}", action=action, default=default, dest=dest)
        else:
            args.add_argument(
                f"--{name}",
                dest=dest,
                action=action,
                nargs=nargs,
                default=default,
                type=parser,
                required=required,
            )

    def register_argparser(
        self, subparsers: argparse._SubParsersAction
    ) -> argparse.ArgumentParser:
        subparser = subparsers.add_parser(name=self.name, description=self.help)
        sig = inspect.signature(self.func)
        params = tuple(sig.parameters.values())

        for param in params:
            self.add_argument(subparser, param)
        subparser.set_defaults(_func_name=self.name)
        return subparser

    def exec(self, args: argparse.Namespace) -> None:
        positionals = []
        keywords = {}
        sig = inspect.signature(self.func)
        for name, param in sig.parameters.items():
            arg = getattr(args, name)
            if parameter.nargs(param) == 1:
                arg = arg[0]
            if param.kind in [param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD]:
                positionals.append(arg)
            elif param.kind == param.VAR_POSITIONAL:
                positionals.extend(arg)
            else:
                keywords[name] = arg
        self.func(*positionals, **keywords)

    def __call__(
        self, *args: Any, **kwds: Any
    ) -> None:
        self.func(*args, **kwds)


class CommandsManager:
    commands: dict[str, Command] = {}

    @classmethod
    def register(cls, name: str, func: F) -> Command:
        cmd = Command(name, func)
        cls.commands[name] = cmd
        return cmd

    @classmethod
    def argparse(cls) -> argparse.ArgumentParser:
        p = argparse.ArgumentParser(
            prog="servctl", description="Easily deploy apps to the server"
        )
        p.add_argument(
            "--config", nargs="?", type=Config.import_from, default="config.yaml"
        )
        sp = p.add_subparsers(title="servctl commands", required=True)
        for cmd in cls.commands.values():
            cmd.register_argparser(sp)
        return p

    @classmethod
    def run(cls) -> None:
        arg_p = cls.argparse()
        args = arg_p.parse_args()
        cmd = cls.commands[args._func_name]
        cmd.exec(args)


def register(name: str) -> Callable[[F], F]:
    def wrap(func: F) -> F:
        CommandsManager.register(name, func)
        return func

    return wrap
