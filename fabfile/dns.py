from pathlib import Path
from typing import Optional
from .context import Context, Config
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


def _add_domain(c: Context, domain: str, force: bool = False) -> None:
    top_domain = ".".join(domain.rsplit(".", maxsplit=2)[-2:])
    top_domain_len = len(top_domain) + 1
    subdomain = domain[:-top_domain_len]
    target_cname = c.app.project.host
    if domain == top_domain:
        warning("A record modification not implemented Yet! Abort")
        return
    client = get_client(c.config)
    try:
        records = client.get(
            f"/domain/zone/{top_domain}/record", fieldType="CNAME", subDomain=subdomain
        )
        if len(records) > 0 and not force:
            warning("domain {} already registered! ignore!".format(domain))
        if len(records) > 0 and force:
            for record in records:
                warning(
                    "domain {} already registered as {}! deleting!".format(
                        domain, record
                    )
                )
                client.delete(f"/domain/zone/{top_domain}/record/{record}")
        if len(records) == 0 or force:
            result = client.post(
                f"/domain/zone/{top_domain}/record",
                fieldType="CNAME",
                subDomain=subdomain,
                target=f"{target_cname}.",
                ttl=0,
            )
            print("OVH DOMAIN CREATE")
            print(json.dumps(result, indent=4))
            client.post(f"/domain/zone/{top_domain}/refresh")

        export_zone(c.config, domain)
    except ovh.exceptions.NotCredential:
        warning("No Credential error! generating new OVH Credential!")
        c.config.ovh.consumer_key = generate_consumer_key(c.config)
        _add_domain(c, domain)


def register_domains(c: Context, force: bool = False, *domains: str) -> None:
    for domain in domains:
        if not domain.startswith("*"):
            _add_domain(c, domain, force=force)


def get_domains(c: Context) -> list[str]:
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
