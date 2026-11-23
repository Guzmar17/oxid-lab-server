#!/usr/bin/env bash
# R11 · Postgres 18 on the Isard desktop `pg` (Default + Wireguard), in Docker, data in /srv/postgres.
#
#   POSTGRES_PASSWORD=… bash deploy/isard/postgres.sh 10.0.29.109     # your VPN address (isard vpn config)
#
# --network host: Postgres sees the real address of whoever connects, and pg_hba.conf decides
# by it. Every desktop and every VPN of the centre is in 10.2.0.0/16: an open 5432 is open to all.
set -euo pipefail

VPN=${1:?"usage: postgres.sh <your VPN address, 10.0.x.y>"}
: "${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD (the superuser's, never in git)}"
HERE=$(cd "$(dirname "$0")" && pwd)

sudo mkdir -p /srv/postgres /etc/ecb
# TODO R11
sleep 3
docker exec postgres psql -U postgres -c "select version()" -c "table pg_hba_file_rules"
