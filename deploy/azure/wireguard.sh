#!/usr/bin/env bash
# R12 · The Azure machine joins Isard's network: the account's WireGuard config as a service that
# comes back after a reboot. Run on your laptop; it copies the file and starts the tunnel there.
#
#   isard vpn config                     # ~/.config/isard/isard-vpn.conf (it holds your private key)
#   isard vpn down                       # one tunnel per account: the laptop's goes, Azure's stays
#   deploy/azure/wireguard.sh ecb-<nom>.francecentral.cloudapp.azure.com
set -euo pipefail

HOST=${1:?"usage: wireguard.sh <host>"}
CONF=${CONF:-$HOME/.config/isard/isard-vpn.conf}

# TODO R12
