from fabfile.context.config import Config
from typing import Union
from fabric import task
import fabric.connection
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


@task
def email_alias(c, alias_f="emails.yaml"):
    # type: (fabric.connection.Connection, str) -> None
    config = Config.config_from_conection(c)
    with open(alias_f) as f:
        emails_c = yaml.load(f.read())
    for domain, emails in emails_c.items():
        print("Generating for:", domain)
        if not emails:
            continue
        emails = {f"{username}@{domain}": alias for username, alias in emails.items()}
        register_email_alias(config, **emails)
        export_zone(config, domain)
