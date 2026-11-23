"""R2 · The tables hold A1's rules: what model.py refused in Polars, the database refuses."""

import psycopg
import pytest
from psycopg import errors

SAMPLE = "insert into lab.sample (id, patient, hospital, specimen, collected_at, received_at) values "


def test_tables_and_owner(admin):
    rows = admin.execute("select tablename, tableowner from pg_tables where schemaname = 'lab'").fetchall()
    assert {row["tablename"] for row in rows} == {"hospital", "patient", "sample", "test", "staff", "report"}
    assert {row["tableowner"] for row in rows} == {"lab_owner"}


def test_keys(admin):
    keys = admin.execute(
        """select tc.table_name, string_agg(kcu.column_name, ',' order by kcu.ordinal_position) as columns
           from information_schema.table_constraints tc
           join information_schema.key_column_usage kcu using (constraint_schema, constraint_name)
           where tc.table_schema = 'lab' and tc.constraint_type = 'PRIMARY KEY' group by 1"""
    ).fetchall()
    assert {row["table_name"]: row["columns"] for row in keys} == {
        "hospital": "code",
        "patient": "code",
        "sample": "id",
        "test": "sample,antibiotic",
        "staff": "login",
        "report": "sample",
    }


@pytest.fixture
def one(admin):
    """A patient and a sample of the test's own (rolled back): no data needed yet."""
    admin.execute("insert into lab.hospital values ('ZZA', 'Hospital de prova', 'Enlloc', 10)")
    admin.execute("insert into lab.patient values ('0000002', 'A', 'B', '1970-01-01', 'D', '08960')")
    admin.execute(SAMPLE + "('ZZA26-00001', '0000002', 'ZZA', 'orina', '2026-01-05 10:00', '2026-01-05 11:00')")
    return admin


def refused(admin, statement: str, error: type[psycopg.Error]) -> None:
    with pytest.raises(error), admin.transaction():
        admin.execute(statement)


def test_patient_rules(admin):
    patient = "insert into lab.patient values "
    refused(admin, patient + "('108818', 'A', 'B', '1970-01-01', 'D', '08960')", errors.CheckViolation)
    refused(admin, patient + "('0000001', 'A', 'B', '1900-01-01', 'D', '08960')", errors.CheckViolation)
    refused(admin, patient + "('0000001', 'A', 'B', '1970-01-01', 'd', '08960')", errors.CheckViolation)
    refused(admin, patient + "('0000001', 'A', 'B', '1970-01-01', 'D', '8960')", errors.CheckViolation)


def test_sample_rules(one):
    admin = one
    values = "'0000002', 'ZZA', 'orina', '2026-01-05 10:00', '2026-01-05 11:00')"
    refused(
        admin,
        SAMPLE + "('ZZA26-00002', '0000002', 'RBX', 'orina', '2026-01-05 10:00', '2026-01-05 11:00')",
        errors.CheckViolation,
    )
    refused(
        admin,
        SAMPLE + "('ZZA26-00002', '0000002', 'ZZA', 'orina', '2026-01-05 10:00', '2026-01-05 09:00')",
        errors.CheckViolation,
    )
    refused(
        admin,
        SAMPLE + "('ZZA26-00002', '0000002', 'ZZA', 'Orina', '2026-01-05 10:00', '2026-01-05 11:00')",
        errors.CheckViolation,
    )
    refused(
        admin,
        SAMPLE + "('ZZA26-00002', '9999999', 'ZZA', 'orina', '2026-01-05 10:00', '2026-01-05 11:00')",
        errors.ForeignKeyViolation,
    )
    refused(admin, SAMPLE + "('ZZA26-00001', " + values, errors.UniqueViolation)


def test_test_rules(one):
    admin = one
    test = "insert into lab.test (sample, antibiotic, mic, mic_censored, diameter, sir) values "
    refused(admin, test + "('ZZA26-00001', 'XXX', null, null, 220, 'S')", errors.CheckViolation)
    refused(admin, test + "('ZZA26-00001', 'XXX', null, null, 20, 's')", errors.CheckViolation)
    refused(admin, test + "('ZZA26-00001', 'XXX', 2, null, 20, 'S')", errors.CheckViolation)
    refused(admin, test + "('ZZA26-00001', 'XXX', 0, false, 20, 'S')", errors.CheckViolation)
    refused(admin, test + "('ZZZ26-00001', 'XXX', 2, false, 20, 'S')", errors.ForeignKeyViolation)
