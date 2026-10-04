#!/usr/bin/env bash
# Start (or restart) Bottleneck Busters in a GitHub Codespace, optionally on another branch.
#
#   bb-start              build and run the checked-out branch
#   bb-start <branch>     fetch <branch>, switch to it, build and run it
#
# Serves the UI and API together on port 8080 behind a shared password (user "bottleneck";
# password from the BB_AUTH_PASSWORD Codespaces secret, else generated once and kept in
# ~/.bb-site-password). The MCP server runs on port 8000. Logs: /tmp/bb/*.log
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"

cd "$(git -C "${CODESPACE_VSCODE_FOLDER:-$PWD}" rev-parse --show-toplevel)"

if [ $# -ge 1 ]; then
  if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Uncommitted changes in $(pwd); commit or stash them before switching." >&2
    exit 1
  fi
  git fetch --quiet origin "$1"
  git checkout --quiet -B "$1" "origin/$1"
fi
branch=$(git rev-parse --abbrev-ref HEAD)

password_file="$HOME/.bb-site-password"
if [ -z "${BB_AUTH_PASSWORD:-}" ]; then
  [ -s "$password_file" ] || python3 -c "import secrets; print(secrets.token_urlsafe(9))" > "$password_file"
  BB_AUTH_PASSWORD=$(cat "$password_file")
fi

pkill -f "uvicorn app\." 2>/dev/null || true
pkill -f "app.mcp_server" 2>/dev/null || true

echo "== $branch @ $(git rev-parse --short HEAD): installing dependencies and building the UI"
(cd frontend && npm ci --no-audit --no-fund --loglevel=error && npm run build --silent)
(cd backend && uv sync --frozen --all-groups --quiet)

mkdir -p /tmp/bb
cd backend
if [ -f app/deploy.py ]; then
  BB_AUTH_PASSWORD="$BB_AUTH_PASSWORD" BB_REQUIRE_AUTH=1 setsid nohup .venv/bin/uvicorn \
    app.deploy:app --host 0.0.0.0 --port 8080 > /tmp/bb/app.log 2>&1 < /dev/null &
  protected=yes
else
  echo "This branch predates app/deploy.py: serving the API only, without a password." >&2
  setsid nohup .venv/bin/uvicorn app.api:app --host 0.0.0.0 --port 8080 \
    > /tmp/bb/app.log 2>&1 < /dev/null &
  protected=no
fi
if [ -f app/mcp_server.py ]; then
  setsid nohup .venv/bin/python -m app.mcp_server --transport streamable-http \
    --host 0.0.0.0 --port 8000 > /tmp/bb/mcp.log 2>&1 < /dev/null &
fi

for _ in $(seq 1 90); do
  curl -sf -o /dev/null http://127.0.0.1:8080/api/health && break
  sleep 1
done
if ! curl -sf -o /dev/null http://127.0.0.1:8080/api/health; then
  echo "The app did not start; last log lines:" >&2
  tail -n 30 /tmp/bb/app.log >&2
  exit 1
fi

url="https://${CODESPACE_NAME:-localhost}-8080.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
cat <<EOF

  Bottleneck Busters is running ($branch).
  App:  $url
EOF
if [ "$protected" = yes ]; then
  echo "  Login: bottleneck / $BB_AUTH_PASSWORD"
fi
cat <<EOF
  To share it: Ports tab > right-click port 8080 > Port Visibility > Public.
  Switch branch: bb-start <branch>   (e.g. bb-start main)
EOF
