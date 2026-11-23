#!/usr/bin/env bash
# This commit to the VM (git archive: nothing uncommitted or ignored goes, no .env), then
# install.sh there.   deploy/azure/push.sh ecb-<nom>.francecentral.cloudapp.azure.com
set -euo pipefail

HOST=${1:?"usage: deploy/azure/push.sh <host>"}
git diff --quiet HEAD || echo "warning: uncommitted changes are not sent, only $(git rev-parse --short HEAD)"
git archive --format=tar HEAD | ssh "azureuser@$HOST" \
  'sudo rm -rf /srv/ecb-lab/next && sudo mkdir -p /srv/ecb-lab/next && sudo tar -x -C /srv/ecb-lab/next'
ssh "azureuser@$HOST" "sudo bash /srv/ecb-lab/next/deploy/azure/install.sh $HOST $(git rev-parse --short HEAD)"
test "$(curl -s -o /dev/null -w '%{http_code}' "https://$HOST/lab/api/me")" = 401 && echo "https://$HOST/lab/ is up"
