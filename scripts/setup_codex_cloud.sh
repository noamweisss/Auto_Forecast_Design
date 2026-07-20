#!/usr/bin/env bash

# Prepare a fresh Codex cloud container for this repository.
# Codex cloud setup scripts run with internet access, while the agent phase may
# not. Installing everything here makes it available during the agent phase.

set -euo pipefail

script_directory="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
forecast_repo_root="$(cd -- "${script_directory}/.." && pwd)"

cd "${forecast_repo_root}"

if ! command -v git >/dev/null 2>&1; then
  echo "Git is required to prepare this repository's committed assets." >&2
  exit 1
fi

if ! command -v git-lfs >/dev/null 2>&1; then
  echo "Git LFS is required to hydrate committed forecast assets." >&2
  echo "Install git-lfs, then rerun this setup script." >&2
  exit 1
fi

git lfs install --local
git lfs pull
git lfs fsck

forecast_python="${FORECAST_PYTHON:-python3}"

if ! command -v "${forecast_python}" >/dev/null 2>&1; then
  echo "Python executable not found: ${forecast_python}" >&2
  echo "Set FORECAST_PYTHON or select Python 3.11+ in the Codex environment." >&2
  exit 1
fi

"${forecast_python}" -m pip install --upgrade pip
"${forecast_python}" -m pip install -r requirements.txt
"${forecast_python}" -m playwright install --with-deps chromium

echo "Codex cloud setup complete."
echo "Run checks with: ${forecast_python} -m pytest tests -q -p no:cacheprovider"
