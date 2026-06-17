#!/bin/bash

set -euo pipefail

TIMEOUT=${SANDBOX_TIMEOUT:-30}
SCRIPT_FILE="/tmp/user_script.sh"

if [ ! -f "$SCRIPT_FILE" ]; then
    echo "Error: No script file found"
    exit 1
fi

chmod +x "$SCRIPT_FILE"

timeout "$TIMEOUT" bash "$SCRIPT_FILE" 2>&1

exit $?