#!/bin/bash
set -e

# 경로 로드
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." &> /dev/null && pwd )"

# 공통 설정
# shellcheck disable=SC1090
source "$PROJECT_ROOT/config.sh"
# shellcheck disable=SC1090
source "$BACKEND_DIR/bin/common_screen.sh"
echo "[config.sh, common_screen.sh] 환경 등록 완료"

# 내부 파이썬 확보
SETUP_PY="$BACKEND_DIR/bin/setup_local_python.sh"
if [ ! -x "$SETUP_PY" ]; then
    echo "내부 파이썬 설치 스크립트를 찾을 수 없습니다: $SETUP_PY" 1>&2
    exit 1
fi
"$SETUP_PY"

# venv 보장
cd "$BACKEND_DIR"
if [ ! -d "$VENV_PATH" ]; then
    "$PY_BIN" -m venv "$VENV_PATH"
fi
# 의존성 설치 커맨드 구성
PIP_INSTALL_CMD=""
if [ -f "$REQUIREMENTS_FILE" ]; then
    PIP_INSTALL_CMD="pip install --no-user -r \"$REQUIREMENTS_FILE\""
fi

# alembic 적용(있으면)
ALEMBIC_CMD=""
if [ -d "$BACKEND_DIR/alembic" ]; then
    ALEMBIC_CMD="alembic upgrade head || true"
fi

# uvicorn 실행
UVICORN_CMD="uvicorn app.main:app --host 0.0.0.0 --port \"$BACKEND_PORT\" --reload"

# screen 내에서 실행할 전체 명령
# BACKEND_SETUP_AND_RUN_COMMAND="source \"$VENV_PATH/bin/activate\" && $PIP_INSTALL_CMD && $ALEMBIC_CMD && $UVICORN_CMD"
BACKEND_SETUP_AND_RUN_COMMAND="source \"$VENV_PATH/bin/activate\" && \
    echo '[Backend Setup] Python 가상 환경 활성화 완료.' && \
    echo '[Backend Setup] 실행: $PIP_INSTALL_CMD' && $PIP_INSTALL_CMD && \
    echo '[Backend Setup] Python 의존성 설치 완료.' && \
    echo '[Backend Setup] 실행: $ALEMBIC_CMD' && $ALEMBIC_CMD && \
    echo '[Backend Setup] Alembic 마이그레이션 적용 완료.' && \
    echo '[Backend Setup] 실행: $UVICORN_CMD' && $UVICORN_CMD"


# screen으로 실행/재시작
start_or_restart_in_screen "$BACKEND_SCREEN_NAME" "$BACKEND_DIR" "$BACKEND_SETUP_AND_RUN_COMMAND"

echo "[백엔드] screen에서 실행 중."
echo "연결: screen -r $BACKEND_SCREEN_NAME"
echo "분리: Ctrl+A D"
