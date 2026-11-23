"""R3 · A1's clean tables into Postgres, with `copy`: one statement per file, not one insert per
row, and the five files in one transaction, so a file that fails leaves nothing half loaded.
"""

from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.rows import tuple_row

from . import config

#: Table → file, in an order where every reference exists before what points at it.
FILES = {
    "hospital": "hospitals.csv",
    "patient": "patients.csv",
    "sample": "samples.csv",
    "test": "tests.csv",
    "staff": "staff.csv",
}


def copy_file(conn: psycopg.Connection, table: str, path: Path) -> None:
    """`path` into `lab.<table>` with `copy … from stdin (format csv, header)`, the columns named
    from the file's header (staff.csv has no token_hash; the order is the file's, not the table's).
    A table or column name is an identifier: it goes in with sql.Identifier, never with %s or an f-string."""
    raise NotImplementedError("R3")


def counts(conn: psycopg.Connection) -> dict[str, int]:
    """Rows per table, as {"hospital": 3, …}."""
    raise NotImplementedError("R3")


def load(conn: psycopg.Connection, data: Path = config.DATA) -> dict[str, int]:
    """Empty the tables and load the five files, all in one transaction; the counts after.
    Run twice, it gives the same counts: a load is not an append."""
    raise NotImplementedError("R3")
