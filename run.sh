#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BDUSS_VAL=$(grep '^export BDUSS=' ~/.zshrc 2>/dev/null | sed 's/^export BDUSS=//')
STOKEN_VAL=$(grep '^export STOKEN=' ~/.zshrc 2>/dev/null | sed 's/^export STOKEN=//')
CAUTH_VAL=$(grep '^export CAUTH=' ~/.zshrc 2>/dev/null | sed 's/^export CAUTH=//')

export BDUSS="${BDUSS_VAL}"
export STOKEN="${STOKEN_VAL}"
export CAUTH="${CAUTH_VAL}"

cd "${SCRIPT_DIR}"
exec python3.11 sync.py "$@"
