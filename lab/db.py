"""R7 · One request, one transaction, one person.

The server logs in as ecb_app, which can do nothing by itself (noinherit). For each request:
the token says who it is (lab.whoami), `set_config('lab.login', …, true)` tells the policies,
and `set local role` gives the person's group its privileges. Both end with the transaction,
so nothing of one request is left on the connection for the next.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import psycopg
from oxid_server import HTTPError
from psycopg import errors, sql
from psycopg.rows import dict_row
from psycopg.types.numeric import FloatLoader
from psycopg.types.string import TextLoader

from . import config

#: The groups a request may become. A role read from the database is checked against this list
#: before it goes into `set role`: an identifier cannot be a parameter.
ROLES = ("clinician", "microbiologist")


@dataclass(frozen=True)
class Person:
    login: str
    role: str
    hospital: str | None


def connect() -> psycopg.Connection:
    """ecb_app's connection (ECB_DATABASE_URL), rows as dicts. JSON has no date and no decimal:
    a timestamp arrives as its text (`2026-01-05 12:50:00`) and a numeric as a float. Given."""
    conn = psycopg.connect(config.need("ECB_DATABASE_URL"), row_factory=dict_row)
    for name in ("timestamp", "timestamptz", "date"):
        conn.adapters.register_loader(name, TextLoader)
    conn.adapters.register_loader("numeric", FloatLoader)
    return conn


def token_of(authorization: str | None) -> str:
    """The token of an `Authorization: Bearer <token>` header; 401 without one."""
    raise NotImplementedError("R7")


def refusal(error: psycopg.Error) -> HTTPError:
    """What a database error means to the client: a privilege or a policy → 403, a duplicate →
    409, a broken rule (check, reference, not null, a malformed value) → 422. Anything else is
    the server's fault and is raised as it is."""
    raise NotImplementedError("R7")


@contextmanager
def request(authorization: str | None) -> Iterator[tuple[psycopg.Connection, Person]]:
    """The connection, in a transaction where the database knows the person; 401 for an unknown
    token. Commits when the block ends, rolls back when it raises; a database error becomes
    refusal()'s HTTPError."""
    raise NotImplementedError("R7")
