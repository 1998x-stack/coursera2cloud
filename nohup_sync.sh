#!/usr/bin/env bash
# =============================================================================
# nohup runner: download & upload all enabled courses in courses.jsonl
#
# Usage:
#   bash nohup_sync.sh          # start in background
#   tail -f logs/sync.log       # watch progress
#   python3 sync.py --status    # check completion status
#
# Status updates:
#   - status.json is updated after EACH course completes
#   - Already-completed courses are automatically skipped
#   - Interrupted runs resume from checkpoint
# =============================================================================

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/logs/sync.log"

cd "${SCRIPT_DIR}"

# Load credentials from ~/.zshrc
BDUSS_VAL=$(grep '^export BDUSS=' ~/.zshrc 2>/dev/null | sed 's/^export BDUSS=//')
STOKEN_VAL=$(grep '^export STOKEN=' ~/.zshrc 2>/dev/null | sed 's/^export STOKEN=//')
CAUTH_VAL=$(grep '^export CAUTH=' ~/.zshrc 2>/dev/null | sed 's/^export CAUTH=//')

export BDUSS="${BDUSS_VAL}"
export STOKEN="${STOKEN_VAL}"
export CAUTH="${CAUTH_VAL}"

# Create log directory
mkdir -p "$(dirname "$LOG_FILE")"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting batch sync..." | tee -a "$LOG_FILE"

nohup python3 sync.py >> "$LOG_FILE" 2>&1 &

PID=$!
echo "PID: $PID"
echo "Log:  $LOG_FILE"
echo "Status: python3 sync.py --status"
echo "Stop:   kill $PID"
