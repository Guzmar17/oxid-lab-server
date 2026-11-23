"""Shared by every test: a Postgres and a RustFS to run against (compose.yaml on your machine,
the pipeline's services in GitLab), the database rebuilt once from nothing by lab.setup, a
token for each of the six staff, and the server called without a socket.

Every test that writes does it inside a transaction it rolls back, or cleans what it made:
the counts the others check stay the data's.
"""

import os
import sys
import warnings
from contextlib import contextmanager
from pathlib import Path

import psycopg
import pytest
from psycopg import sql
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# The tests' own settings, before anything reads them; a .env does not override these.
ADMIN = os.environ.setdefault("ECB_ADMIN_URL", "postgresql://postgres:password@localhost:5432/postgres")
os.environ.setdefault("ECB_APP_PASSWORD", "app-test-password")
os.environ.setdefault("ECB_BACKUP_PASSWORD", "backup-test-password")
for prefix in ("ECB_S3", "ECB_BACKUP_S3"):
    os.environ.setdefault(f"{prefix}_ENDPOINT", "http://localhost:9000")
    os.environ.setdefault(f"{prefix}_ACCESS_KEY", "admin")
    os.environ.setdefault(f"{prefix}_SECRET_KEY", "password")
os.environ.setdefault("ECB_REPORTS_BUCKET", "ecb-reports-test")
os.environ.setdefault("ECB_BACKUP_BUCKET", "ecb-backup-test")


def url(user: str, password: str, database: str = "ecb") -> str:
    return psycopg.conninfo.make_conninfo(ADMIN, user=user, password=password, dbname=database)


def url_admin(database: str) -> str:
    return psycopg.conninfo.make_conninfo(ADMIN, dbname=database)


os.environ.setdefault("ECB_DATABASE_URL", url("ecb_app", os.environ["ECB_APP_PASSWORD"]))
os.environ.setdefault("ECB_BACKUP_URL", url("ecb_backup", os.environ["ECB_BACKUP_PASSWORD"]))

STAFF = ["laia.puig", "oriol.mas", "pau.serra", "marta.vidal", "jordi.camps", "nuria.roca"]


@pytest.fixture(scope="session")
def loaded():
    """lab.setup.run(), once: the counts it answered. Before R3 is written the tables are built
    and empty (None here), so R1 and R2 can be tested already. A SQL file that fails stops the
    setup there: what it says is in the warnings at the end, and the tests run on what was built."""
    from lab import setup

    try:
        return setup.run()
    except NotImplementedError:
        return None
    except psycopg.Error as error:
        warnings.warn(f"lab.setup stopped: {error}", stacklevel=1)
        return None


@pytest.fixture(scope="session")
def tokens(loaded):
    """login → its token, issued as the superuser."""
    from lab import staff

    with psycopg.connect(url_admin("ecb")) as conn:
        return {login: staff.issue(conn, login) for login in STAFF}


@pytest.fixture
def admin(loaded):
    """The superuser in `ecb`, inside a transaction that is rolled back."""
    with psycopg.connect(url_admin("ecb"), row_factory=dict_row) as conn:
        yield conn
        conn.rollback()


@contextmanager
def as_person(login: str | None, role: str):
    """ecb_app as the server makes it, without lab.db: the login in lab.login, `set local role`.
    Rolled back at the end. `login=None` sets no lab.login at all."""
    with psycopg.connect(os.environ["ECB_DATABASE_URL"], row_factory=dict_row) as conn:
        if login is not None:
            conn.execute("select set_config('lab.login', %s, true)", [login])
        conn.execute(sql.SQL("set local role {}").format(sql.Identifier(role)))
        yield conn
        conn.rollback()


@pytest.fixture
def person(loaded):
    return as_person


@pytest.fixture(scope="session")
def s3():
    """The admin's S3 client, and the two test buckets, made empty."""
    from lab import storage

    client = storage.client()
    for bucket in (os.environ["ECB_REPORTS_BUCKET"], os.environ["ECB_BACKUP_BUCKET"]):
        try:
            client.create_bucket(Bucket=bucket)
        except client.exceptions.BucketAlreadyOwnedByYou, client.exceptions.BucketAlreadyExists:
            pass
        for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket):
            for item in page.get("Contents", []):
                client.delete_object(Bucket=bucket, Key=item["Key"])
    return client


@pytest.fixture(scope="session")
def client(tokens, s3):
    from oxid_server.testing import Client

    import server

    return Client(server.app)


@pytest.fixture(scope="session")
def auth(tokens):
    """auth("laia.puig") → the headers of a request as Laia."""
    return lambda login: [("authorization", f"Bearer {tokens[login]}")]


def count(conn, query: str, params=()) -> int:
    row = conn.execute(query, params).fetchone()
    return next(iter(row.values())) if isinstance(row, dict) else row[0]
