"""R9 · Reports: the PDF in RustFS, its key and SHA-256 in Postgres, served back only if intact."""

import hashlib
import os

import pytest

PDF = b"%PDF-1.4\n% ECB A2 test report\n1 0 obj << /Type /Catalog >> endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n"


def test_the_key():
    from lab import storage

    assert storage.key_of("RBX", "RBX26-00001") == "RBX/RBX26-00001.pdf"


def test_upload_and_read_back(client, auth, s3, admin):
    answer = client.put("/api/samples/RBX26-00002/report", body=PDF, headers=auth("jordi.camps"))
    assert answer.status == 200
    expected = {"object_key": "RBX/RBX26-00002.pdf", "sha256": hashlib.sha256(PDF).hexdigest(), "bytes": len(PDF)}
    assert answer.json() == expected
    head = s3.head_object(Bucket=os.environ["ECB_REPORTS_BUCKET"], Key="RBX/RBX26-00002.pdf")
    assert head["ContentType"] == "application/pdf"
    row = admin.execute("select uploaded_by, bytes from lab.report where sample = 'RBX26-00002'").fetchone()
    assert row == {"uploaded_by": "jordi.camps", "bytes": len(PDF)}

    read = client.get("/api/samples/RBX26-00002/report", headers=auth("laia.puig"))
    assert read.status == 200 and read.body == PDF
    assert read.header("content-type") == "application/pdf"
    assert client.get("/api/samples/RBX26-00002/report", headers=auth("pau.serra")).status == 404
    assert client.get("/api/samples/RBX26-00003/report", headers=auth("laia.puig")).status == 404
    assert client.get("/api/samples/RBX26-00002", headers=auth("laia.puig")).json()["report"] is True


def test_refused(client, auth):
    assert client.put("/api/samples/RBX26-00004/report", body=b"hello", headers=auth("jordi.camps")).status == 415
    assert client.put("/api/samples/RBX26-00004/report", body=PDF, headers=auth("laia.puig")).status == 403
    assert client.put("/api/samples/RBX26-99999/report", body=PDF, headers=auth("jordi.camps")).status == 404


def test_a_changed_object_is_not_served(client, auth, s3):
    from lab import storage

    assert client.put("/api/samples/CSA26-00003/report", body=PDF, headers=auth("nuria.roca")).status == 200
    s3.put_object(Bucket=os.environ["ECB_REPORTS_BUCKET"], Key="CSA/CSA26-00003.pdf", Body=PDF + b"tampered")
    with pytest.raises(ValueError):
        storage.get_report(s3, "CSA/CSA26-00003.pdf", hashlib.sha256(PDF).hexdigest())
