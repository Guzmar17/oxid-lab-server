"""A person's token for the server: made here once, shown once, stored only as its SHA-256.

    uv run python -m lab.staff laia.puig      # as the superuser (ECB_ADMIN_URL); prints the token

Given complete.
"""

import hashlib
import secrets
import sys

import psycopg

from . import config


def digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue(conn: psycopg.Connection, login: str) -> str:
    """A new token for `login`, replacing the old one; a login that does not exist raises."""
    token = secrets.token_urlsafe(32)
    updated = conn.execute("update lab.staff set token_hash = %s where login = %s", [digest(token), login])
    if updated.rowcount != 1:
        raise LookupError(f"no such staff: {login}")
    return token


if __name__ == "__main__":
    from .setup import admin

    config.load_dotenv()
    with admin(config.DATABASE) as conn:
        print(issue(conn, sys.argv[1]))
