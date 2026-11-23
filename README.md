# ecb-lab-server

ECB · C044 · A2-P1. El servidor de la Xarxa de microbiologia del Riubaix: les dades de l'A1 a
Postgres, amb rols, privilegis de columna i seguretat a nivell de fila; els informes en PDF i
les còpies de la base de dades a RustFS. El servidor és a la màquina d'Azure de l'A1; Postgres i
els tres nodes de RustFS són a Isard, i Azure hi arriba per la VPN WireGuard d'Isard.

```
   navegador / curl ──HTTPS──▶ Azure: Caddy ─▶ oxid-server (server.py)      ─┐
                                       └─ ecb-backup.timer (lab.backup)    │ WireGuard
                                                                           ▼ 10.2.0.0/16
                         Isard: pg (Postgres 18)    rustfs-1 (nginx :80) ── rustfs-2, rustfs-3
                                                                (xarxa Personal 10.0.0.0/24)
```

## A la teva màquina

```sh
docker compose up -d                 # Postgres 18 i RustFS, com a Isard
cp .env.example .env                 # i posa-hi les teves contrasenyes
uv sync
uv run python -m lab.setup           # la base de dades des de zero: rols, taules, privilegis, polítiques, dades
uv run pytest tests/test_r1_roles.py # un requisit
uv run pytest                        # tots
uv run python -m lab.staff laia.puig # un token per a la Laia (només es veu un cop)
uv run oxid-server server.py --runtime cpython   # http://127.0.0.1:8000
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/api/me
```

Les proves refan la base de dades `ecb` cada cop: no hi guardis res que vulguis conservar.

## On és cada cosa

| | |
|---|---|
| `db/1_roles.sql` … `4_policies.sql` | els rols, les taules, els privilegis i les polítiques, en l'ordre en què `lab.setup` els executa |
| `lab/setup.py` | (fet) la base de dades des de zero, com a superusuari |
| `lab/load.py` | les dades amb `copy` |
| `lab/db.py` | una petició: el token, la persona, la transacció |
| `server.py` | les rutes |
| `lab/storage.py` | els informes a RustFS |
| `lab/backup.py` | la còpia de la base de dades a RustFS, i la restauració |
| `lab/staff.py`, `lab/config.py` | (fets) els tokens; l'entorn |
| `deploy/isard/` | Postgres, els tres nodes, nginx, els usuaris de RustFS |
| `deploy/azure/` | WireGuard, els serveis, el temporitzador de la còpia |
| `data/` | les dades (`data/README.md`) |

## Les rutes

Totes demanen `Authorization: Bearer <token>`; sense, 401.

| | | |
|---|---|---|
| `GET` | `/api/me` | qui ets |
| `GET` | `/api/samples?organism=&limit=` | les mostres que pots veure |
| `GET` | `/api/samples/{id}` | una mostra, el seu pacient i les seves proves |
| `POST` | `/api/samples` | un clínic registra una mostra del seu hospital |
| `PUT` | `/api/samples/{id}/tests/{antibiotic}` | un microbiòleg registra un resultat |
| `GET` | `/api/resistance?organism=` | taxes de resistència per hospital i antibiòtic |
| `PUT` | `/api/samples/{id}/report` | un microbiòleg puja l'informe en PDF |
| `GET` | `/api/samples/{id}/report` | l'informe |
