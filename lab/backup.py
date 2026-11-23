"""R10 · The database's copy, in RustFS: every table as CSV under `<stamp>/`, and a manifest.json
with each table's rows and SHA-256. Made as ecb_backup, which reads everything (bypassrls).

    uv run python -m lab.backup                  # a copy now (ECB_BACKUP_URL, ECB_BACKUP_S3_*)
    uv run python -m lab.backup restore [STAMP]  # into a new database ecb_restore, checked (superuser)

A copy that is never restored is a hope, not a copy: restore() checks every table against the manifest.
"""

import hashlib
import json
import os
import sys
from datetime import UTC, datetime

import psycopg
from psycopg import sql

from . import config, storage
from .load import FILES

TABLES = [*FILES, "report"]


def bucket() -> str:
    return os.environ.get("ECB_BACKUP_BUCKET", "ecb-backup")


def stamp_now() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def dump(conn: psycopg.Connection, s3, stamp: str) -> dict:
    """Every table of TABLES to `<stamp>/<table>.csv` (copy … to stdout, csv with header), then
    `<stamp>/manifest.json`: {"stamp": …, "tables": {table: {"rows": n, "sha256": hex}}}.

    - `row_security = off`: a role that RLS would filter gets an error, not a partial copy that
      looks whole (what pg_dump does).
    - One read-only repeatable read transaction: every table from the same instant."""
    raise NotImplementedError("R10")


def latest(s3) -> str:
    """The newest whole copy: the newest stamp (a "folder" at the bucket's root, a listing with
    Delimiter="/") that has its manifest.json. The manifest is written last, so a copy that
    failed halfway has CSVs and no manifest, and is not a copy."""
    raise NotImplementedError("R10")


def restore(conn: psycopg.Connection, s3, stamp: str) -> dict[str, int]:
    """The copy `stamp` into the (empty) database `conn` is connected to, in one transaction;
    each file's SHA-256 and each table's rows checked against the manifest (ValueError if not).
    Returns the rows per table."""
    raise NotImplementedError("R10")


def main(argv: list[str]) -> None:
    config.load_dotenv()
    s3 = storage.client("ECB_BACKUP_S3")
    if argv[:1] == ["restore"]:
        from . import setup

        stamp = argv[1] if len(argv) > 1 else latest(s3)
        setup.create("ecb_restore")
        with setup.admin("ecb_restore") as conn:
            print(stamp, restore(conn, s3, stamp))
        return
    with psycopg.connect(config.need("ECB_BACKUP_URL")) as conn:
        manifest = dump(conn, s3, stamp_now())
    print(manifest["stamp"], {table: entry["rows"] for table, entry in manifest["tables"].items()})


if __name__ == "__main__":
    main(sys.argv[1:])
