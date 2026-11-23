#!/usr/bin/env bash
# R11 · On rustfs-1, once the cluster says `Disks: 3 (3 online)`: the two buckets, versioning on
# the backups, and one user per program with only its policy. admin is never in a .env.
#
#   APP_SECRET=… BACKUP_SECRET=… bash deploy/isard/rustfs.sh      # rc alias `cluster` set first
set -euo pipefail
: "${APP_SECRET:?}" "${BACKUP_SECRET:?}"
HERE=$(cd "$(dirname "$0")" && pwd)

rc admin info cluster cluster | sed -n "/Servers/,/EC Parity/p"
# TODO R11
rc admin user info cluster/ ecb-app
rc admin user info cluster/ ecb-backup
