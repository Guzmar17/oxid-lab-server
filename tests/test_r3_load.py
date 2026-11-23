"""R3 · The five files with `copy`, in one transaction, twice the same."""

import shutil

import psycopg
import pytest

from conftest import count, url_admin

COUNTS = {"hospital": 3, "patient": 896, "sample": 2122, "test": 6783, "staff": 6}


def test_counts(loaded):
    assert loaded == COUNTS


def test_codes_keep_their_zeros(admin):
    assert count(admin, "select count(*) from lab.patient where code like '0%%'") == 133
    row = admin.execute(
        "select mic::float as mic from lab.test where sample = 'CSA26-00001' and antibiotic = 'CAZ'"
    ).fetchone()
    assert row == {"mic": 4.0}


def test_twice_is_the_same(admin):
    from lab import load

    admin.execute("select 1")  # the fixture's transaction is open: load's becomes a savepoint, rolled back after
    assert load.load(admin) == COUNTS
    assert load.load(admin) == COUNTS


def test_a_bad_file_loads_nothing(tmp_path, loaded):
    from lab import config, load

    data = tmp_path / "data"
    shutil.copytree(config.DATA, data)
    with (data / "tests.csv").open("a", encoding="utf-8") as file:
        file.write("RBX26-00001,ZZZ,1.0,false,20,X\n")  # sir X: the check refuses it
    with psycopg.connect(url_admin("ecb")) as conn:
        with pytest.raises(psycopg.errors.CheckViolation):
            load.load(conn, data)
        conn.rollback()
        assert load.counts(conn) == COUNTS
