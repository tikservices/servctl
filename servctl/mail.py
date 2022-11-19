from pathlib import Path
from .commands import register
from .context.config import Config
from typing import Union, Optional
from logging import warning
import ovh
import json
from .dns import generate_consumer_key, get_client, export_zone
import yaml


def _add_email_alias(conf: Config, alias: str, email: str) -> None:
    client = get_client(conf)
    _, top_domain = alias.split("@")
    try:
        result = client.post(
            f"/email/domain/{top_domain}/redirection",
            **{
                "from": alias,
                "localCopy": False,
                "to": email,
            },
        )
        print("OVH Email Alias CREATE")
        print(json.dumps(result, indent=4))
        # client.post('/domain/zone/tik.tn/refresh')
    except ovh.exceptions.NotCredential:
        warning("No Credential error! generating new OVH Credential!")
        conf.ovh.consumer_key = generate_consumer_key(conf)
        _add_email_alias(conf, alias, email)
    except ovh.exceptions.ResourceConflictError:
        warning(f"Alias {alias} for {email} already registered! ignore!")


def register_email_alias(conf: Config, **alias: Union[str, list[str]]) -> None:
    for e_alias, emails in alias.items():
        if isinstance(emails, str):
            email = emails
            _add_email_alias(conf, e_alias, email)
        elif isinstance(emails, list):
            for email in emails:
                _add_email_alias(conf, e_alias, email)


@register(name="email:alias")
def email_alias(config: Config, alias_f: Union[Path, str] = "emails.yaml") -> None:
    with Path(alias_f).open() as f:
        emails_c = yaml.safe_load(f.read())
    for domain, emails in emails_c.items():
        print("Generating for:", domain)
        if not emails:
            continue
        emails = {f"{username}@{domain}": alias for username, alias in emails.items()}
        register_email_alias(config, **emails)
        export_zone(config, domain)


@register(name="email:aliases")
def register_aliases(config: Config, alias_f: Optional[Union[Path, str]] = None) -> None:
    if alias_f:
        register_alias(config, Path(alias_f))
    else:
        aliases_d = Path("aliases/")
        assert aliases_d.is_dir(), "aliases/ folder should exists and contains aliases files"
        aliases_f = [f for f in aliases_d.iterdir() if f.is_file()]
        for alias_f in aliases_f:
            register_alias(config, alias_f)


def register_alias(config: Config, alias_f: Path) -> None:
    with alias_f.open() as f:
        emails = yaml.safe_load(f.read())
    domain = alias_f.name
    print("Generating for:", domain)
    if not emails:
        return
    emails = {f"{username}@{domain}": alias for username, alias in emails.items()}
    register_email_alias(config, **emails)
    export_zone(config, domain)
