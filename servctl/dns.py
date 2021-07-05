from pathlib import Path
from typing import Optional
from .context import Context, Config, ContextWithApp
from . import server
from logging import warning
import ovh
import json


def generate_consumer_key(config: Config) -> str:
    client = ovh.Client(
        endpoint=config.ovh.endpoint,
        application_key=config.ovh.application_key,
        application_secret=config.ovh.application_secret,
    )
    ck = client.new_consumer_key_request()
    ck.add_rules(ovh.API_READ_ONLY, "/me")
    ck.add_recursive_rules(ovh.API_READ_WRITE, "/domain/zone")
    ck.add_recursive_rules(ovh.API_READ_WRITE, "/email/domain")
    req = ck.request()

    print("Please visit {} to authenticate".format(req["validationUrl"]))
    input("and press Enter to continue...")

    print("Key generated for", client.get("/me")["firstname"])
    print("consumerKey = '{}'".format(req["consumerKey"]))
    return str(req["consumerKey"])


__client: Optional[ovh.Client] = None


def get_client(config: Config) -> ovh.Client:
    global __client
    if not __client:
        __client = ovh.Client(
            endpoint=config.ovh.endpoint,
            application_key=config.ovh.application_key,
            application_secret=config.ovh.application_secret,
            consumer_key=config.ovh.consumer_key,
        )
    return __client


def _can_create_record(c: ContextWithApp, domain: str, top_domain: str, subdomain: str, force: bool) -> bool:
    client = get_client(c.config)
    if domain == top_domain:
        records = client.get(
            f"/domain/zone/{top_domain}/record", fieldType="A",
        )
    else:
        records = client.get(
            f"/domain/zone/{top_domain}/record", fieldType="CNAME", subDomain=subdomain
        )
    if len(records) > 0 and not force:
        warning("domain {} already registered! ignore!".format(domain))
        return False
    elif len(records) > 0 and force:
        for record in records:
            warning(
                "domain {} already registered as {}! deleting!".format(
                    domain, record
                )
            )
            client.delete(f"/domain/zone/{top_domain}/record/{record}")
    return True

def _add_cname_entry(c: ContextWithApp, domain: str, top_domain: str, force: bool) -> Optional[dict]:
    client = get_client(c.config)
    target_cname = c.app.project.host
    top_domain_len = len(top_domain) + 1
    subdomain = domain[:-top_domain_len]
    if not _can_create_record(c, domain, top_domain, subdomain, force):
        return None
    record = client.post(
        f"/domain/zone/{top_domain}/record",
        fieldType="CNAME",
        subDomain=subdomain,
        target=f"{target_cname}.",
        ttl=0,
    )
    return record


def _add_a_entry(c: ContextWithApp, domain: str, force: bool) -> Optional[dict]:
    client = get_client(c.config)
    if not _can_create_record(c, domain, domain, "", force):
        return None
    server_if = server.get_server_default_interface(c)
    server_ip = server_if.get("address", None)
    assert server_ip, "Server ip address was not detected"
    record = client.post(
        f"/domain/zone/{domain}/record",
        fieldType="A",
        target=server_ip,
        subDomain="",
        ttl=0,
    )
    return record


def _add_domain(c: ContextWithApp, domain: str, force: bool = False) -> None:
    top_domain = ".".join(domain.rsplit(".", maxsplit=2)[-2:])
    try:
        if domain == top_domain:
            record = _add_a_entry(c, domain, force)
        else:
            record = _add_cname_entry(c, domain, top_domain, force)
    except ovh.exceptions.NotCredential:
        warning("No Credential error! generating new OVH Credential!")
        c.config.ovh.consumer_key = generate_consumer_key(c.config)
        _add_domain(c, domain)
        return

    if record:
        print("OVH DOMAIN CREATED")
        print(json.dumps(record, indent=4))
        client = get_client(c.config)
        client.post(f"/domain/zone/{top_domain}/refresh")
        export_zone(c.config, domain)



def register_domains(c: ContextWithApp, force: bool = False, *domains: str) -> None:
    for domain in domains:
        if not domain.startswith("*"):
            _add_domain(c, domain, force=force)
    # force dns cache flush/refresh
    c.sh.sudo("resolvectl flush-caches")


def get_domains(c: ContextWithApp) -> list[str]:
    domains = []
    for domain in c.app.domains:
        domains.append(domain)
        if not domain.startswith("*"):
            domains.append("www." + domain)
    return domains


def export_zone(config: Config, domain: str) -> None:
    top_domain = ".".join(domain.rsplit(".", maxsplit=2)[-2:])
    client = get_client(config)
    zone_txt = client.get(f"/domain/zone/{top_domain}/export")
    zone_l = zone_txt.splitlines()
    zone_l[2:] = sorted(zone_l[2:])
    zone_f = Path("zones") / top_domain
    zone_f.parent.mkdir(exist_ok=True)
    with zone_f.open("w") as f:
        f.write("\n".join(zone_l))
