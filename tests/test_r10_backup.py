"""R10 · The copy: every table, checked, restored into a database of its own; never partial."""

import json
import os

import psycopg
import pytest

from conftest import url, url_admin

COUNTS = {"hospital": 3, "patient": 896, "sample": 2122, "test": 6783, "staff": 6}
STAMP = "20261124T030000Z"


@pytest.fixture(scope="module")
def copy(tokens, s3):
    from lab import backup

    with psycopg.connect(os.environ["ECB_BACKUP_URL"]) as conn:
        return backup.dump(conn, s3, STAMP)


def test_the_manifest(copy, s3):
    bucket = os.environ["ECB_BACKUP_BUCKET"]
    assert copy["stamp"] == STAMP
    assert {table: entry["rows"] for table, entry in copy["tables"].items() if table != "report"} == COUNTS
    assert json.loads(s3.get_object(Bucket=bucket, Key=f"{STAMP}/manifest.json")["Body"].read()) == copy
    keys = {item["Key"] for item in s3.list_objects_v2(Bucket=bucket, Prefix=f"{STAMP}/")["Contents"]}
    assert keys == {f"{STAMP}/{table}.csv" for table in [*COUNTS, "report"]} | {f"{STAMP}/manifest.json"}


def test_never_partial(loaded, admin):
    """A role without bypassrls that can read every table: the policies would hide rows, so the copy must fail."""
    from lab import backup, storage

    admin.execute("create role partial login password 'partial'")
    admin.execute("grant connect on database ecb to partial")
    admin.execute("grant usage on schema lab to partial")
    admin.execute("grant select on all tables in schema lab to partial")
    admin.commit()
    try:
        with (
            psycopg.connect(url("partial", "partial")) as conn,
            pytest.raises(psycopg.errors.InsufficientPrivilege, match="row-level security"),
        ):
            backup.dump(conn, storage.client("ECB_BACKUP_S3"), "20261124T040000Z")
    finally:
        admin.rollback()
        admin.execute("drop owned by partial")
        admin.execute("drop role partial")
        admin.commit()


def test_latest(copy, s3):
    from lab import backup

    bucket = os.environ["ECB_BACKUP_BUCKET"]
    s3.put_object(Bucket=bucket, Key="20261101T030000Z/manifest.json", Body=b"{}")
    s3.put_object(Bucket=bucket, Key="20261130T030000Z/hospital.csv", Body=b"code\n")  # failed halfway: no manifest
    assert backup.latest(s3) == STAMP


def test_restore(copy, s3):
    from lab import backup, setup

    setup.create("ecb_restore")
    with psycopg.connect(url_admin("ecb_restore")) as conn:
        restored = backup.restore(conn, s3, STAMP)
    assert {table: rows for table, rows in restored.items() if table != "report"} == COUNTS


def test_a_changed_file_is_not_restored(copy, s3):
    from lab import backup, setup

    bucket = os.environ["ECB_BACKUP_BUCKET"]
    other = "20261125T030000Z"
    for name in [*copy["tables"], "manifest"]:
        suffix = "json" if name == "manifest" else "csv"
        s3.copy_object(Bucket=bucket, Key=f"{other}/{name}.{suffix}", CopySource=f"{bucket}/{STAMP}/{name}.{suffix}")
    s3.put_object(Bucket=bucket, Key=f"{other}/test.csv", Body=b"sample,antibiotic,mic,mic_censored,diameter,sir\n")
    setup.create("ecb_restore")
    try:
        with psycopg.connect(url_admin("ecb_restore")) as conn, pytest.raises(ValueError, match="test.csv"):
            backup.restore(conn, s3, other)
    finally:
        for name in [*copy["tables"], "manifest"]:
            s3.delete_object(Bucket=bucket, Key=f"{other}/{name}.{'json' if name == 'manifest' else 'csv'}")
        setup.drop("ecb_restore")
