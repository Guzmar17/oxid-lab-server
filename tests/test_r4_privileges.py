"""R4 · Privileges: a login without privileges, PUBLIC with nothing, each group only its own."""

import os

import psycopg
import pytest
from psycopg import errors

from conftest import url


def test_the_app_alone_reads_nothing(loaded):
    with psycopg.connect(os.environ["ECB_DATABASE_URL"]) as conn, pytest.raises(errors.InsufficientPrivilege):
        conn.execute("select count(*) from lab.hospital")


def test_public_has_nothing(admin):
    admin.execute("create role nobody login password 'nobody'")
    admin.commit()
    try:
        with pytest.raises(psycopg.OperationalError, match="permission denied"):  # not even connect
            psycopg.connect(url("nobody", "nobody")).close()
        functions = admin.execute(
            """select p.proname from pg_proc p join pg_namespace n on n.oid = p.pronamespace
               where n.nspname = 'lab' and has_function_privilege('nobody', p.oid, 'execute')"""
        ).fetchall()
        assert functions == []
        tables = admin.execute(
            """select relname from pg_class where relnamespace = 'lab'::regnamespace
               and relkind in ('r', 'v') and has_table_privilege('nobody', oid, 'select')"""
        ).fetchall()
        assert tables == []
    finally:
        admin.rollback()
        admin.execute("drop role nobody")
        admin.commit()


@pytest.mark.parametrize(
    ("role", "login", "statement"),
    [
        ("clinician", "laia.puig", "update lab.test set sir = 'R' where sample = 'RBX26-00001'"),
        ("clinician", "laia.puig", "select count(*) from lab.staff"),
        ("clinician", "laia.puig", "delete from lab.sample where id = 'RBX26-00001'"),
        (
            "microbiologist",
            "jordi.camps",
            (
                "insert into lab.sample (id, patient, hospital, specimen, collected_at, received_at)"
                " values ('RBX26-99999', '0108818', 'RBX', 'orina', now(), now())"
            ),
        ),
        ("microbiologist", "jordi.camps", "select token_hash from lab.staff"),
        ("microbiologist", "jordi.camps", "update lab.sample set hospital = 'OLV' where id = 'RBX26-00001'"),
    ],
)
def test_what_a_group_cannot_do(person, role, login, statement):
    with person(login, role) as conn, pytest.raises(errors.InsufficientPrivilege):
        conn.execute(statement)


def test_the_backup_reads_and_writes_nothing(loaded):
    with psycopg.connect(os.environ["ECB_BACKUP_URL"]) as conn:
        assert conn.execute("select count(*) from lab.staff").fetchone() == (6,)
        with pytest.raises(errors.InsufficientPrivilege):
            conn.execute("delete from lab.report")
