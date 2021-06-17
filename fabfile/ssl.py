from pathlib import Path
from .context.config import Config
from .utils import render
from .context import Context
from fabric import task
import fabric.connection


def generate_for_domains(c: Context, *domain_names: str) -> None:
    domains = remove_reduntancy(domain_names)
    wildcard = any([d.startswith("*") for d in domains])
    if wildcard:
        ovh_p = generate_ovh_ini(c)
        cmd = f"certbot certonly --dns-ovh --dns-ovh-credentials {ovh_p}"
    else:
        cmd = "certbot --nginx"
        ovh_p = None
    cmd += " --expand -d '{}'".format(",".join(domains))
    cmd += f" --cert-name {c.app.project.name}"
    cmd += f" --agree-tos --email {c.config.webmaster.email} -n"
    c.sh.sudo(cmd)
    if ovh_p:
        c.sh.rm(ovh_p)


def remove_reduntancy(r_domains: tuple[str]) -> list[str]:
    parent_domains: dict[str, set[str]] = {}
    for domain in r_domains:
        p_domain = domain.split(".", 1)[1]
        try:
            parent_domains[p_domain].add(domain)
        except KeyError:
            parent_domains[p_domain] = {domain}
    domains: list[str] = []
    for p_domain, c_domains in parent_domains.items():
        if f"*.{p_domain}" in c_domains:
            domains.append(f"*.{p_domain}")
        else:
            domains.extend(c_domains)
    return domains


def generate_ovh_ini(c: Context) -> str:
    from tempfile import NamedTemporaryFile

    dst = "/tmp/ovh.ini"
    t = c.config.dirs.local.template / "ovh" / "ovh.ini.jinja2"
    res = render(c, t)
    with NamedTemporaryFile("w") as f:
        f.write(res)
        f.flush()
        c.sh.put(f.name, dst)
        return dst


@task
def generate_all(c):
    # type: (fabric.connection.Connection) -> None
    domains = []
    domains_f = Path("zones") / "domains.txt"
    domains_f.parent.mkdir(exist_ok=True)
    domains_f.touch(exist_ok=True)
    with domains_f.open("r") as f:
        for d in f.readlines():
            domain = d.split("#", 1)[0].strip()
            if domain:
                domains.append(domain)
    c.sudo(
        "certbot --nginx --expand -d '{domains}' --agree-tos \
         --email {email} -n".format(
            domains=",".join(domains), email=c.config.webmaster.email
        )
    )


@task
def renew(c):
    # type: (fabric.connection.Connection) -> None
    conf = Config.config_from_conection(c)
    ovh_p = generate_ovh_ini(Context(config=conf, app=None, con=c, sh=None))  # type: ignore
    c.sudo("certbot renew")
    c.run(f"rm {ovh_p} -rf")
