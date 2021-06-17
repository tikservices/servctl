from .context import Context
from github import Github, GithubException


def create_push_webhook(c: Context) -> None:
    if not c.app.repo.private:
        print("Skiping webhook registration")
        return
    g = Github(c.config.github.access_token)
    r = g.get_repo(c.app.repo.path)
    hooks = r.get_hooks()
    hook_url = f"https://{c.app.project.host}/github_update"
    if not any([h.config["url"] == hook_url for h in hooks]):
        r.create_hook(
            "web",
            {
                "content_type": "json",
                "url": hook_url,
                "secret": c.config.github.webhook_secret,
            },
            events=["push"],
            active=True,
        )


def register_deploy_key(c: Context) -> None:
    if not c.app.repo.private:
        print("Skiping deploy key registration")
        return
    g = Github(c.config.github.access_token)
    r = g.get_repo(c.app.repo.path)
    fingerprint = c.con.sudo(
        f" ssh-keygen -l -E sha256 -f {c.app.repo.deploy_key}.pub", user="www-data"
    ).stdout
    # key_name = os.path.basename(c.app.repo.deploy_key)
    key_name = f"{c.app.project.host} {fingerprint}"
    keys = r.get_keys()
    if not any([k.title == key_name for k in keys]):
        key_content = c.con.sudo(
            f"cat {c.app.repo.deploy_key}.pub", user="www-data"
        ).stdout
        try:
            r.create_key(key_name, key_content, read_only=True)
        except TypeError:
            r.create_key(key_name, key_content)
        except GithubException:
            print("Key already deployed")


def clone(c: Context) -> None:
    project_dir = c.app.project.src_dir
    branch = c.app.repo.branch
    clone_cmd_cl = "git clone {project_repo_url} --single-branch -b {branch}\
    {project_dir} --recurse-submodules".format(
        project_repo_url=c.app.repo.url,
        project_dir=project_dir,
        branch=branch,
    )
    clone_cmd_pl = "git -C {project_dir} pull && git -C {project_dir} submodule update --init --recursive --rebase".format(
        project_dir=project_dir,
    )
    if c.app.repo.private:
        gen_deploy_key(c)
        clone_cmd_cl = 'ssh-agent bash -c "ssh-add {deploy_key} && {clone_cmd}"'.format(
            deploy_key=c.app.repo.deploy_key, clone_cmd=clone_cmd_cl
        )
        clone_cmd_pl = 'ssh-agent bash -c "ssh-add {deploy_key} && {clone_cmd}"'.format(
            deploy_key=c.app.repo.deploy_key, clone_cmd=clone_cmd_pl
        )
    if not c.sh.sudo(clone_cmd_cl, user="www-data", warn=True):
        c.sh.sudo(clone_cmd_pl, user="www-data")


def gen_deploy_key(c: Context) -> None:
    key_p = c.app.repo.deploy_key
    if not key_p or c.sh.exists(key_p):
        return
    c.sh.mkdir(key_p.parent, owner="www-data", mode=0o700)
    c.sh.sudo(
        'ssh-keygen -t ed25519 -C "{email}" -f {key} -N ""'.format(
            email=c.config.webmaster.email, key=key_p
        ),
        user="www-data",
    )
