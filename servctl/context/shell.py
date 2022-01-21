from .app import App
from pathlib import Path
from typing import Literal, Optional, Union
from fabric.connection import Connection
import invoke.runners
from patchwork.files import exists
import shlex


class Shell:
    def __init__(self, con: Connection) -> None:
        self.con = con

    def run(
        self,
        cmd: str,
        env: Optional[dict[str, str]] = None,
        cwd: Optional[Union[str, Path]] = None,
        pty: bool = False,
    ) -> None:
        cmd = self._build_cmd(cmd, cwd=cwd, env=env)
        self.con.run(cmd, env=env, pty=pty)

    @staticmethod
    def _build_cmd(
        cmd: str,
        cwd: Optional[Union[str, Path]] = None,
        env: Optional[dict[str, str]] = None,
    ) -> str:
        if env:
            params = shlex.join(
                ["{}={}".format(k, v) for k, v in sorted(env.items())]
            )
            cmd = f"export {params} && {cmd}"

        if cwd:
            cd = shlex.join(['cd', str(cwd)])
            cmd = f"{cd} && {cmd}"
        if env or cwd:
            cmd = shlex.join(["bash", "-i", "-c", cmd])
        return cmd

    def sudo(
        self,
        cmd: str,
        user: Optional[str] = None,
        warn: bool = False,
        pty: bool = False,
        env: Optional[dict[str, str]] = None,
        cwd: Optional[Union[str, Path]] = None,
    ) -> bool:
        res = self._sudo(cmd, user=user, warn=warn, pty=pty, env=env, cwd=cwd)
        if warn:
            return bool(res.ok)
        else:
            return True

    def _sudo(
        self,
        cmd: str,
        user: Optional[str] = None,
        warn: bool = False,
        pty: bool = False,
        env: Optional[dict[str, str]] = None,
        cwd: Optional[Union[str, Path]] = None,
    ) -> invoke.runners.Result:
        cmd = self._build_cmd(cmd, cwd=cwd, env=env)
        return self.con.sudo(cmd, user=user, env=env, warn=warn, pty=pty)

    def ln(
        self, src: Union[Path, str], dst: Union[Path, str], force: bool = False
    ) -> None:
        cmd = f"ln -s --no-dereference {src} {dst}"
        if force:
            cmd += " -f"
        self.sudo(cmd)

    def mv(self, src: Union[Path, str], dst: Union[Path, str]) -> None:
        cmd = f"mv {src} {dst}"
        self.sudo(cmd)

    def mkdir(
        self,
        p: Union[Path, str],
        owner: Optional[str] = None,
        group: Optional[str] = None,
        mode: Optional[Union[int, str]] = None,
    ) -> None:
        cmd = f"mkdir -p {p}"
        self.sudo(cmd)
        if owner:
            self.chown(p, owner, group=group)
        if mode is not None:
            self.chmod(p, mode, recursive=False)

    def rm(self, p: Union[Path, str]) -> None:
        cmd = f"rm -rf {p}"
        self.sudo(cmd)

    def put(self, src_l: Union[Path, str], dst_r: Union[Path, str]) -> None:
        self.con.put(str(src_l), str(dst_r))

    def get(self, src_r: Union[Path, str], dst_l: Union[Path, str], use_sudo: bool = False) -> None:
        Path(dst_l).parent.mkdir(parents=True, exist_ok=True)
        self.con.get(str(src_r), str(dst_l))  # FIXME, use_sudo=use_sudo)

    def chown(
        self, dst_r: Union[Path, str], owner: str, group: Optional[str] = None
    ) -> None:
        if not group:
            group = owner
            self.sudo(f"chown -R {owner}:{group} {dst_r}")

    def chmod(
        self, dst_r: Union[Path, str], mode: Union[int, str], recursive: bool = False
    ) -> None:
        cmd = "chmod"
        if recursive:
            cmd += " -R"
        if isinstance(mode, str):
            self.sudo(f"{cmd} {mode} {dst_r}")
        else:
            self.sudo(f"{cmd} {mode:o} {dst_r}")

    def upload(
        self,
        src_l: Union[Path, str],
        dst_r: Union[Path, str],
        owner: Optional[str] = None,
        group: Optional[str] = None,
        mode: Optional[Union[int, str]] = None,
    ) -> None:
        file_n = Path(src_l).name
        self.put(src_l, f"/tmp/{file_n}")
        self.mv(f"/tmp/{file_n}", dst_r)
        if owner:
            self.chown(dst_r, owner, group=group)
        if mode is not None:
            self.chmod(dst_r, mode)

    def upload_etc(
        self,
        app: App,
        src_l: Union[Path, str],
        dst_r: Union[Path, str],
        owner: Optional[str] = None,
        group: Optional[str] = None,
        mode: Optional[Union[int, str]] = None,
    ) -> None:
        file_n = Path(src_l).name
        etc_f = app.project.etc_dir / file_n
        self.upload(src_l, etc_f, owner=owner, group=group, mode=mode)
        self.ln(etc_f, dst_r, force=True)
        if owner:
            self.chown(dst_r, owner, group=group)
        if mode is not None:
            self.chmod(dst_r, mode)

    def exists(self, p: Union[str, Path]) -> bool:
        return bool(exists(self.con, path=str(p), runner=self.con.sudo, ))

    def systemd(
        self,
        action: Literal["enable", "disable", "start", "stop", "restart", "reload"],
        service: Optional[str] = None,
    ) -> None:
        if action == "reload":
            self.sudo("systemctl daemon-reload")
        else:
            assert service, "Service name not specified for systemctl"
            self.sudo(f"systemctl {action} {service}")
