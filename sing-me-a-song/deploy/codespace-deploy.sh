#!/usr/bin/env bash
# Deploys the sing-me-a-song back-end inside a GitHub Codespace.
#
# Usage (from your machine, with the gh CLI authenticated):
#   gh codespace create -R <owner>/<repo> -b 0827-faeh-singasong --idle-timeout 4h
#   gh codespace ssh -c <codespace-name> -- bash /workspaces/<repo>/sing-me-a-song/deploy/codespace-deploy.sh
#   gh codespace ports visibility 5000:public -c <codespace-name>
#
# The API is then reachable at: https://<codespace-name>-5000.app.github.dev
set -euo pipefail

cd "$(dirname "$0")/../back-end"

echo "==> Starting PostgreSQL (docker)"
if ! docker ps --format '{{.Names}}' | grep -q '^sms-postgres$'; then
  docker rm -f sms-postgres >/dev/null 2>&1 || true
  docker run -d --name sms-postgres -p 5432:5432 \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=sing_me_a_song \
    postgres:14-alpine
fi
until docker exec sms-postgres pg_isready -U postgres >/dev/null 2>&1; do sleep 1; done
echo "==> PostgreSQL is ready"

echo "==> Writing back-end .env"
cat > .env <<EOF
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sing_me_a_song
PORT=5000
EOF

echo "==> Installing dependencies"
npm ci

echo "==> Applying database migrations"
npx prisma migrate deploy

echo "==> Building"
npm run build

echo "==> Starting server"
pkill -f "node dist/server.js" 2>/dev/null || true
sleep 1
nohup npm start > server.log 2>&1 &
sleep 5
curl -sf http://localhost:5000/recommendations >/dev/null
echo "==> Back-end is up on port 5000"
