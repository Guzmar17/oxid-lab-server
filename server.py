"""R8 · The network's server: every route is one request of lab.db, so what a person sees and
may write is decided by the database (privileges, column privileges, policies), not here.

    uv run oxid-server server.py --runtime cpython          # http://127.0.0.1:8000

Not one route answers anything the database did not let the person read: a query never asks
for a column the person's group cannot read, and a sample the policy hides is 404, as if it
did not exist (a 403 would tell that it does).
"""

from oxid_server import App, HTTPError, Response

from lab import config, db, storage

config.load_dotenv()
app = App(title="ecb-lab-server")
S3 = storage.client()

ORGANISMS = ("ECO", "KPN", "PAE", "SAU", "EFA")

#: Below this many tests a rate is not published (A1's R11): None, with its n.
MIN_N = 30

#: The patient's columns each group may read (3_privileges.sql); select * would fail for a microbiologist.
PATIENT_COLUMNS = {
    "clinician": "p.code, p.given_name, p.family_name, p.birth_date, p.sex",
    "microbiologist": "p.code, p.birth_date, p.sex",
}


def visible(conn, sample_id: str) -> dict:
    """The sample if the person may see it; 404 otherwise, the same answer whether it exists or not."""
    row = conn.execute("select * from lab.sample where id = %s", [sample_id]).fetchone()
    if row is None:
        raise HTTPError(404, f"no such sample: {sample_id}")
    return row


@app.get("/api/me")
async def me(headers):
    """Who the token is: login, role, hospital (null for a microbiologist)."""
    raise NotImplementedError("R8")


@app.get("/api/samples")
async def samples(headers, organism: str = "", limit: int = 50):
    """The samples the person may see, newest first, at most `limit` (1–500, else 422):
    id, hospital, patient, specimen, collected_at, reported_at, organism. `organism` filters."""
    raise NotImplementedError("R8")


@app.get("/api/samples/{sample_id}")
async def sample(headers, sample_id: str):
    """One sample with its patient (the columns the person's group may read), its tests
    (antibiotic, mic, mic_censored, diameter, sir, by antibiotic) and whether it has a report."""
    raise NotImplementedError("R8")


@app.post("/api/samples", body=True)
async def register(headers, body):
    """A clinician registers a sample of their hospital: {id, patient, specimen, collected_at,
    received_at}, hospital = the id's three letters. 201 with the row; another hospital's → 403
    (the policy), an existing id → 409, a broken rule or an unknown patient → 422."""
    raise NotImplementedError("R8")


@app.put("/api/samples/{sample_id}/tests/{antibiotic}", body=True)
async def result(headers, sample_id: str, antibiotic: str, body):
    """A microbiologist records one antibiotic's result: {mic, mic_censored, diameter, sir}
    (insert, or update when the test exists). A clinician → 403; a sample not seen → 404."""
    raise NotImplementedError("R8")


@app.get("/api/resistance")
async def resistance(headers, organism: str = "ECO"):
    """Per hospital and antibiotic of `organism`: tested, resistant and rate (resistant / tested,
    3 decimals), the rate null below MIN_N tests; 404 for an organism the network does not report.
    One query for everybody: the policy decides which hospitals it counts."""
    raise NotImplementedError("R8")


@app.put("/api/samples/{sample_id}/report", body=bytes)
async def put_report(headers, sample_id: str, body):
    """R9 · A microbiologist uploads the sample's PDF report (the body, application/pdf): to
    RustFS under storage.key_of, then its row in lab.report (replaced if there was one).
    Not a PDF → 415; a clinician → 403; a sample not seen → 404. Answers object_key, sha256, bytes."""
    raise NotImplementedError("R9")


@app.get("/api/samples/{sample_id}/report")
async def get_report(headers, sample_id: str):
    """R9 · The sample's PDF, read from RustFS by the server (the bucket is never public, and
    RustFS is reachable only through WireGuard) and checked against its SHA-256. 404 without one."""
    raise NotImplementedError("R9")
