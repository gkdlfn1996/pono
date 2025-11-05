#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
BACKEND_BIN="$SCRIPT_DIR"

"$BACKEND_BIN/pono_backend.sh"
"$BACKEND_BIN/pono_frontend.sh"

echo "=== 모든 서버가 screen 세션에서 실행 중입니다 ==="
