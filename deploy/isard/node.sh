#!/usr/bin/env sh
# R11 · One RustFS node of three (data/rustfs, "Arranca los nodos"): run on rustfs-1, -2 and -3,
# each with the Personal network at 10.0.0.1N and the three names in /etc/hosts.
#
#   RUSTFS_SECRET_KEY=… sh deploy/isard/node.sh
set -eu
: "${RUSTFS_SECRET_KEY:?set RUSTFS_SECRET_KEY (the cluster's admin password, never in git)}"
sudo mkdir -p /srv/rustfs
sudo chown 10001:10001 /srv/rustfs
docker rm -f rustfs >/dev/null 2>&1 || true
# TODO R11
