"""R8 · The server: the same routes for everybody, the database deciding what each one sees."""

import pytest

NEW = {"patient": "0108818", "specimen": "orina", "collected_at": "2026-11-24 10:00", "received_at": "2026-11-24 11:00"}


def test_me(client, auth):
    assert client.get("/api/me").status == 401
    assert client.get("/api/me", headers=[("authorization", "Bearer nope")]).status == 401
    me = client.get("/api/me", headers=auth("laia.puig")).json()
    assert me == {"login": "laia.puig", "role": "clinician", "hospital": "RBX"}
    assert client.get("/api/me", headers=auth("nuria.roca")).json()["hospital"] is None


def test_samples(client, auth):
    rows = client.get("/api/samples?limit=500", headers=auth("pau.serra")).json()
    assert len(rows) == 500 and {row["hospital"] for row in rows} == {"OLV"}
    assert set(rows[0]) == {"id", "hospital", "patient", "specimen", "collected_at", "reported_at", "organism"}
    assert rows[0]["collected_at"] >= rows[-1]["collected_at"]
    network = client.get("/api/samples?organism=KPN&limit=500", headers=auth("jordi.camps")).json()
    assert {row["organism"] for row in network} == {"KPN"}
    assert {row["hospital"] for row in network} == {"RBX", "OLV", "CSA"}
    assert client.get("/api/samples?limit=0", headers=auth("jordi.camps")).status == 422
    assert client.get("/api/samples?limit=501", headers=auth("jordi.camps")).status == 422


def test_one_sample(client, auth):
    assert client.get("/api/samples/OLV26-00001", headers=auth("laia.puig")).status == 404
    assert client.get("/api/samples/XXX26-00001", headers=auth("laia.puig")).status == 404
    clinician = client.get("/api/samples/OLV26-00001", headers=auth("pau.serra")).json()
    assert set(clinician["patient"]) == {"code", "given_name", "family_name", "birth_date", "sex"}
    antibiotics = [test["antibiotic"] for test in clinician["tests"]]
    assert antibiotics and antibiotics == sorted(antibiotics)
    microbiologist = client.get("/api/samples/OLV26-00001", headers=auth("jordi.camps"))
    assert microbiologist.status == 200
    assert set(microbiologist.json()["patient"]) == {"code", "birth_date", "sex"}


def test_register(client, auth, admin):
    try:
        made = client.post("/api/samples", json=NEW | {"id": "RBX26-90001"}, headers=auth("laia.puig"))
        assert made.status == 201 and made.json()["hospital"] == "RBX"
        assert client.post("/api/samples", json=NEW | {"id": "RBX26-90001"}, headers=auth("oriol.mas")).status == 409
        assert client.post("/api/samples", json=NEW | {"id": "OLV26-90001"}, headers=auth("laia.puig")).status == 403
        assert client.post("/api/samples", json=NEW | {"id": "RBX26-90002"}, headers=auth("jordi.camps")).status == 403
        unknown = NEW | {"id": "RBX26-90003", "patient": "9999999"}
        assert client.post("/api/samples", json=unknown, headers=auth("laia.puig")).status == 422
        late = NEW | {"id": "RBX26-90004", "received_at": "2026-11-24 09:00"}
        assert client.post("/api/samples", json=late, headers=auth("laia.puig")).status == 422
        assert client.post("/api/samples", json={"id": "RBX26-90005"}, headers=auth("laia.puig")).status == 422
    finally:
        admin.execute("delete from lab.sample where id like 'RBX26-9000_'")
        admin.commit()


def test_a_result(client, auth, admin):
    url = "/api/samples/CSA26-00002/tests/FOS"
    body = {"mic": 0.5, "mic_censored": False, "diameter": 24, "sir": "S"}
    try:
        answer = client.put(url, json=body, headers=auth("nuria.roca"))
        assert answer.status == 200 and answer.json()["sir"] == "S"
        assert client.put(url, json=body | {"sir": "R"}, headers=auth("nuria.roca")).json()["sir"] == "R"
        assert client.put(url, json=body, headers=auth("marta.vidal")).status == 403
        assert client.put(url, json=body | {"sir": "X"}, headers=auth("nuria.roca")).status == 422
        assert client.put("/api/samples/CSA26-99999/tests/FOS", json=body, headers=auth("nuria.roca")).status == 404
    finally:
        admin.execute("delete from lab.test where antibiotic = 'FOS'")
        admin.commit()


def test_resistance(client, auth):
    network = client.get("/api/resistance?organism=ECO", headers=auth("jordi.camps")).json()
    cip = {row["hospital"]: row for row in network if row["antibiotic"] == "CIP"}
    assert set(cip) == {"CSA", "OLV", "RBX"}
    assert all(
        row["rate"] == pytest.approx(row["resistant"] / row["tested"], abs=0.0005)
        for row in network
        if row["rate"] is not None
    )
    efa = client.get("/api/resistance?organism=EFA", headers=auth("jordi.camps")).json()
    assert {row["hospital"] for row in efa if row["rate"] is None} == {"CSA"}  # 15 tests each
    assert all(row["rate"] is not None for row in efa if row["tested"] >= 30)
    mine = client.get("/api/resistance?organism=ECO", headers=auth("marta.vidal")).json()
    assert {row["hospital"] for row in mine} == {"CSA"}
    assert [row for row in network if row["hospital"] == "CSA"] == mine
    assert client.get("/api/resistance?organism=XYZ", headers=auth("jordi.camps")).status == 404
