#!/usr/bin/env bash
# Push using GITHUB_TOKEN from .env (useful when moving between machines).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Missing .env – copy .env.example to .env and add GITHUB_TOKEN."
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

if [[ -z "${GITHUB_TOKEN:-}" || "${GITHUB_TOKEN}" == "ghp_your_token_here" ]]; then
  echo "Set a real GITHUB_TOKEN in .env first."
  exit 1
fi

USERNAME="${GITHUB_USERNAME:-shira-ozana}"
BRANCH="${1:-$(git branch --show-current)}"
REMOTE_URL="https://${USERNAME}:${GITHUB_TOKEN}@github.com/shira-ozana/career-ai.git"

echo "Pushing branch: ${BRANCH}"
git push "$REMOTE_URL" "HEAD:refs/heads/${BRANCH}"
echo "Done."
