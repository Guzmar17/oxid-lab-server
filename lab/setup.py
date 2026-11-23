"""The database from nothing: drop it, the roles, the schema, the privileges, the policies,
the data. Run it as the superuser, from your machine or CI, never from the server.

    uv run python -m lab.setup          # ECB_ADMIN_URL, ECB_APP_PASSWORD, ECB_BACKUP_PASSWORD

Given complete: read it to see the order in which your SQL files run.
"""

import psycopg
from psycopg import sql

from . import config, load


def admin(database: str = "postgres", **kwargs) -> psycopg.Connection:
    """A superuser connection to `database`, from ECB_ADMIN_URL (whatever database it names)."""
    url = psycopg.conninfo.make_conninfo(config.need("ECB_ADMIN_URL"), dbname=database)
    return psycopg.connect(url, **kwargs)


def script(name: str) -> str:
    return (config.SQL / name).read_text(encoding="utf-8")


def schema(database: str) -> None:
    """Tables, privileges and policies in `database`, in one transaction: all or nothing."""
    with admin(database) as conn:
        conn.execute(sql.SQL("revoke all on database {} from public").format(sql.Identifier(database)))
        conn.execute(sql.SQL("grant connect on database {} to ecb_app, ecb_backup").format(sql.Identifier(database)))
        for name in ["2_schema.sql", "3_privileges.sql", "4_policies.sql"]:
            conn.execute(script(name))


def roles() -> None:
    """The cluster's roles (1_roles.sql) and their passwords. `alter role … password` takes no
    parameter (`%s`): the password goes in as a literal, quoted by psycopg, never pasted."""
    with admin(autocommit=True) as conn:
        conn.execute(script("1_roles.sql"))
        for role, variable in [("ecb_app", "ECB_APP_PASSWORD"), ("ecb_backup", "ECB_BACKUP_PASSWORD")]:
            password = sql.Literal(config.need(variable))
            conn.execute(sql.SQL("alter role {} password {}").format(sql.Identifier(role), password))


def drop(database: str) -> None:
    with admin(autocommit=True) as conn:
        conn.execute(sql.SQL("drop database if exists {} with (force)").format(sql.Identifier(database)))


def create(database: str) -> None:
    """An empty database with the whole schema: what a restore (lab.backup) writes into."""
    drop(database)
    with admin(autocommit=True) as conn:
        conn.execute(sql.SQL("create database {}").format(sql.Identifier(database)))
    schema(database)


def run() -> dict[str, int]:
    drop(config.DATABASE)
    drop("ecb_restore")  # a restore's database also holds objects of these roles
    roles()
    create(config.DATABASE)
    with admin(config.DATABASE) as conn:
        return load.load(conn)


if __name__ == "__main__":
    config.load_dotenv()
    print(run())
