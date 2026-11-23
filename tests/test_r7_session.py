"""R7 · lab.db: the token, the person, the transaction, and what an error means."""

import pytest
from oxid_server import HTTPError

from conftest import count

NEW = """insert into lab.sample (id, patient, hospital, specimen, collected_at, received_at)
         values (%s, '0108818', %s, %s, '2026-11-24 10:00', '2026-11-24 11:00')"""


@pytest.mark.parametrize("header", [None, "", "Bearer", "Bearer   ", "Basic bGFpYTp4", "token abc"])
def test_no_token_is_401(header):
    from lab import db

    with pytest.raises(HTTPError) as raised:
        db.token_of(header)
    assert raised.value.status == 401


def test_the_token():
    from lab import db

    assert db.token_of("Bearer abc") == "abc"
    assert db.token_of("bearer abc") == "abc"


def test_an_unknown_token_is_401(tokens):
    from lab import db

    with pytest.raises(HTTPError) as raised, db.request("Bearer not-a-token"):
        pass
    assert raised.value.status == 401


def test_the_request_is_the_person(tokens):
    from lab import db

    with db.request(f"Bearer {tokens['laia.puig']}") as (conn, person):
        assert person == db.Person("laia.puig", "clinician", "RBX")
        row = conn.execute("select current_user, session_user, current_setting('lab.login') as login").fetchone()
        assert row == {"current_user": "clinician", "session_user": "ecb_app", "login": "laia.puig"}


def test_it_ends_with_the_transaction(tokens):
    """set local and set_config(…, true): after the commit, the same connection is nobody again."""
    from lab import db

    with db.request(f"Bearer {tokens['jordi.camps']}") as (conn, _person):
        conn.commit()
        row = conn.execute("select current_user, current_setting('lab.login', true) as login").fetchone()
        assert row == {"current_user": "ecb_app", "login": ""}


@pytest.mark.parametrize(
    ("login", "values", "status"),
    [
        ("laia.puig", ["OLV26-99998", "OLV", "orina"], 403),
        ("laia.puig", ["RBX26-00001", "RBX", "orina"], 409),
        ("laia.puig", ["RBX26-99998", "RBX", "saliva"], 422),
        ("jordi.camps", ["RBX26-99998", "RBX", "orina"], 403),
    ],
)
def test_what_an_error_means(tokens, admin, login, values, status):
    from lab import db

    with pytest.raises(HTTPError) as raised, db.request(f"Bearer {tokens[login]}") as (conn, _person):
        conn.execute(NEW, values)
    assert raised.value.status == status
    assert count(admin, "select count(*) from lab.sample where id like '%%-9999_'") == 0


def test_a_written_row_stays(tokens, admin):
    from lab import db

    try:
        with db.request(f"Bearer {tokens['oriol.mas']}") as (conn, _person):
            conn.execute(NEW, ["RBX26-99997", "RBX", "orina"])
        assert count(admin, "select count(*) from lab.sample where id = 'RBX26-99997'") == 1
    finally:
        admin.execute("delete from lab.sample where id = 'RBX26-99997'")
        admin.commit()
