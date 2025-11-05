#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." &> /dev/null && pwd )"

# shellcheck disable=SC1090
source "$PROJECT_ROOT/config.sh"
# shellcheck disable=SC1090
source "$PROJECT_ROOT/backend/bin/common_screen.sh"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "프론트엔드 디렉토리를 찾을 수 없습니다: $FRONTEND_DIR" 1>&2
    exit 1
fi

# 필요시 npm 스크립트명 변경 (예: npm run dev / npm run serve)
FRONTEND_SETUP_AND_RUN_COMMAND="npm install && npm run serve"

start_or_restart_in_screen "$FRONTEND_SCREEN_NAME" "$FRONTEND_DIR" "$FRONTEND_SETUP_AND_RUN_COMMAND"

echo "[프론트엔드] screen에서 실행 중."
echo "연결: screen -r $FRONTEND_SCREEN_NAME"
echo "분리: Ctrl+A D"
