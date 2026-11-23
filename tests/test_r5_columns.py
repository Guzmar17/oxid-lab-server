"""R5 · A microbiologist reads a patient's code, birth date and sex, never a name or a postcode."""

import pytest
from psycopg import errors


def test_the_columns_a_microbiologist_reads(person):
    with person("jordi.camps", "microbiologist") as conn:
        assert len(conn.execute("select code, birth_date, sex from lab.patient").fetchall()) == 896


@pytest.mark.parametrize(
    "query",
    ["select * from lab.patient", "select given_name from lab.patient", "select count(postcode) from lab.patient"],
)
def test_the_columns_a_microbiologist_does_not(person, query):
    with person("jordi.camps", "microbiologist") as conn, pytest.raises(errors.InsufficientPrivilege):
        conn.execute(query)


def test_a_clinician_reads_the_whole_patient(person):
    with person("laia.puig", "clinician") as conn:
        row = conn.execute("select * from lab.patient limit 1").fetchone()
        assert set(row) == {"code", "given_name", "family_name", "birth_date", "sex", "postcode"}


def test_privileges_name_the_columns(admin):
    columns = admin.execute(
        """select column_name from information_schema.column_privileges
           where table_schema = 'lab' and table_name = 'patient' and grantee = 'microbiologist'
             and privilege_type = 'SELECT' order by 1"""
    ).fetchall()
    assert [row["column_name"] for row in columns] == ["birth_date", "code", "sex"]
