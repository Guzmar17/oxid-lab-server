"""Every address and secret comes from the environment (`.env` locally, `/etc/ecb-lab.env` on
Azure), never from the code: a file in git is public, also in an old commit. Given complete.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SQL = ROOT / "db"

#: The database's name: the same on Isard, in CI and on your machine.
DATABASE = "ecb"


def need(name: str) -> str:
    """An environment variable that must be set; its absence stops the program here, saying which."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set (see .env.example)")
    return value


def load_dotenv(path: Path = ROOT / ".env") -> None:
    """`KEY=value` lines of `.env` into the environment, without overriding what is already set."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())
