from typing import Iterable, Optional
from .commands import register
from .utils import render
from .context import Context, ContextWithApp


def generate_for_domains(c: ContextWithApp, *domain_names: str) -> None:
    domains = remove_reduntancy(domain_names)
    wildcard = any([d.startswith("*") for d in domains])
    ovh_p: Optional[str]
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


def remove_reduntancy(r_domains: Iterable[str]) -> list[str]:
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


@register(name="ssl:renew")
def renew(c: Context) -> None:
    ovh_p = generate_ovh_ini(c)
    c.sh.sudo("certbot renew")
    c.sh.rm(ovh_p)
