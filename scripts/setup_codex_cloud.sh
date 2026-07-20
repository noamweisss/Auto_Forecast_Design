#!/usr/bin/env bash

# Prepare a fresh Codex cloud container for this repository.
# Codex cloud setup scripts run with internet access, while the agent phase may
# not. Installing everything here makes it available during the agent phase.

set -euo pipefail

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
