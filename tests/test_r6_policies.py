"""R6 · Row level security: a clinician's hospital, the whole network for a microbiologist."""

import pytest
from psycopg import errors

from conftest import count

NEW = """insert into lab.sample (id, patient, hospital, specimen, collected_at, received_at)
         values (%s, '0108818', %s, 'orina', '2026-11-24 10:00', '2026-11-24 11:00')"""


@pytest.mark.parametrize(
    ("login", "hospital", "samples"),
    [("laia.puig", "RBX", 924), ("pau.serra", "OLV", 748), ("marta.vidal", "CSA", 450)],
)
def test_a_clinician_sees_their_hospital(person, login, hospital, samples):
    with person(login, "clinician") as conn:
        rows = conn.execute("select hospital, count(*) from lab.sample group by 1").fetchall()
        assert rows == [{"hospital": hospital, "count": samples}]


def test_the_other_tables_follow_the_sample(person, admin):
    patients = count(admin, "select count(distinct patient) from lab.sample where hospital = 'RBX'")
    tests = count(
        admin, "select count(*) from lab.test t join lab.sample s on s.id = t.sample where s.hospital = 'RBX'"
    )
    with person("laia.puig", "clinician") as conn:
        assert count(conn, "select count(*) from lab.patient") == patients == 423
        assert count(conn, "select count(*) from lab.test") == tests
        assert count(conn, "select count(*) from lab.test where sample like 'OLV%%'") == 0


def test_a_microbiologist_sees_the_network(person):
    with person("jordi.camps", "microbiologist") as conn:
        assert count(conn, "select count(*) from lab.sample") == 2122
        assert count(conn, "select count(*) from lab.test") == 6783


def test_nobody_set_sees_nothing(person):
    with person(None, "clinician") as conn:
        assert count(conn, "select count(*) from lab.sample") == 0
    with person("jordi.camps", "clinician") as conn:  # a microbiologist's login has no hospital
        assert count(conn, "select count(*) from lab.sample") == 0


def test_a_clinician_writes_only_their_hospital(person):
    with person("laia.puig", "clinician") as conn:
        conn.execute(NEW, ["RBX26-99999", "RBX"])
        assert count(conn, "select count(*) from lab.sample where id = 'RBX26-99999'") == 1
    with (
        person("laia.puig", "clinician") as conn,
        pytest.raises(errors.InsufficientPrivilege, match="row-level security"),
    ):
        conn.execute(NEW, ["OLV26-99999", "OLV"])


def test_forced_for_the_owner(admin):
    rows = admin.execute(
        """select relname, relrowsecurity, relforcerowsecurity from pg_class
           where relnamespace = 'lab'::regnamespace and relkind = 'r'"""
    ).fetchall()
    forced = {row["relname"] for row in rows if row["relrowsecurity"] and row["relforcerowsecurity"]}
    assert forced == {"sample", "test", "patient", "report"}


def test_a_clinician_cannot_ask_who_is_who(person):
    with person("laia.puig", "clinician") as conn, pytest.raises(errors.InsufficientPrivilege):
        conn.execute("select * from lab.whoami('x')")
