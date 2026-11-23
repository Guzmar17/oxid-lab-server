#!/usr/bin/env bash
# On the VM, as root (push.sh runs it): next/ becomes app/, synced, the services restarted.
# The A1 machine and its Caddy: A1 stays at /, this server answers under /lab/.
set -euo pipefail

HOST=${1:?host}
COMMIT=${2:-unknown}
ROOT=/srv/ecb-lab
export UV_PYTHON_INSTALL_DIR=/opt/uv/python UV_CACHE_DIR=/var/cache/uv

id ecb >/dev/null 2>&1 || useradd --system --home /srv ecb
for file in /etc/ecb-lab.env /etc/ecb-backup.env; do
  [ -f "$file" ] || { echo "missing $file (see .env.example)"; exit 1; }
  chmod 600 "$file"
done
rm -rf "$ROOT/app" && mv "$ROOT/next" "$ROOT/app"
cd "$ROOT/app"
uv sync --frozen --no-dev
echo "$COMMIT" > commit.txt
chown -R ecb:ecb "$ROOT/app"
chmod -R a+rX /opt/uv

install -m 644 deploy/azure/ecb-lab.service deploy/azure/ecb-backup.service deploy/azure/ecb-backup.timer /etc/systemd/system/
printf '%s {\n\thandle_path /lab/* {\n\t\treverse_proxy 127.0.0.1:8001\n\t}\n\treverse_proxy 127.0.0.1:8000\n}\n' "$HOST" > /etc/caddy/Caddyfile
systemctl daemon-reload
systemctl enable ecb-lab ecb-backup.timer >/dev/null 2>&1
systemctl restart ecb-lab
systemctl start ecb-backup.timer
systemctl reload caddy || systemctl restart caddy

for _ in $(seq 30); do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8001/api/me || true)
  [ "$code" = 401 ] && { echo "ecb-lab $COMMIT is serving"; exit 0; }
  sleep 1
done
journalctl -u ecb-lab -n 40 --no-pager
exit 1
