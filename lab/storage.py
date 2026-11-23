"""R9 · The reports' PDFs in RustFS (S3), never in Postgres and never on the server's disk.

One bucket, `ECB_REPORTS_BUCKET`, private. The key is `<hospital>/<sample>.pdf`; the database
keeps the key and the SHA-256, so a report read back can be checked against what was stored.
"""

import hashlib
import os

import boto3
from botocore.config import Config

from . import config


def client(prefix: str = "ECB_S3"):
    """A boto3 S3 client from `<prefix>_ENDPOINT`, `<prefix>_ACCESS_KEY`, `<prefix>_SECRET_KEY`
    (the server's user is not the backup's: each has only the policy it needs). Given complete."""
    return boto3.client(
        "s3",
        endpoint_url=config.need(f"{prefix}_ENDPOINT"),
        aws_access_key_id=config.need(f"{prefix}_ACCESS_KEY"),
        aws_secret_access_key=config.need(f"{prefix}_SECRET_KEY"),
        region_name="us-east-1",
        config=Config(s3={"addressing_style": "path"}, retries={"max_attempts": 3}),
    )


def bucket() -> str:
    return os.environ.get("ECB_REPORTS_BUCKET", "ecb-reports")


def key_of(hospital: str, sample: str) -> str:
    """`RBX/RBX26-00001.pdf`."""
    raise NotImplementedError("R9")


def put_report(s3, hospital: str, sample: str, pdf: bytes) -> dict:
    """Store the PDF under its key with its type, application/pdf; returns
    {"object_key": …, "sha256": hex, "bytes": n}. Not a PDF (it does not start with `%PDF-`) → ValueError."""
    raise NotImplementedError("R9")


def get_report(s3, key: str, sha256: str) -> bytes:
    """The PDF back; if its SHA-256 is not the one the database kept → ValueError (it is not
    what was stored: never serve it)."""
    raise NotImplementedError("R9")
