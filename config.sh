#!/bin/bash

# --- PONO 프로젝트 공통 환경 변수 ---


# 프로젝트 루트 경로를 이 설정 파일이 위치한 디렉토리로 동적으로 설정
# 이 파일이 start_dev.sh와 같은 디렉토리에 있다고 가정합니다.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
export PROJECT_ROOT="$SCRIPT_DIR"

# Python 설치 경로 및 버전
PY_VER="3.10.13"                                    # Python 버전
PY_PREFIX="$PROJECT_ROOT/.python/python-$PY_VER"    # 최종 설치 루트
PY_BIN="$PY_PREFIX/bin/python3.10"                  # 최종 실행 파일
SRC_DIR="$PROJECT_ROOT/.python/src"                 # 소스/빌드 위치
TGZ_PATH="$SRC_DIR/Python-$PY_VER.tgz"              # 내려받을 아카이브
TGZ_URL="https://www.python.org/ftp/python/$PY_VER/Python-$PY_VER.tgz"


# 프로젝트 하위 디렉토리 경로
export BACKEND_DIR="$PROJECT_ROOT/backend"
export FRONTEND_DIR="$PROJECT_ROOT/frontend"

# 가상 환경 및 의존성 파일 경로
export VENV_PATH="$BACKEND_DIR/.venv"
export REQUIREMENTS_FILE="$BACKEND_DIR/requirements.txt"

# Screen 세션 이름 (모든 환경에서 일관되게 사용)
export BACKEND_SCREEN_NAME="pono_backend"
export FRONTEND_SCREEN_NAME="pono_frontend"

# 애플리케이션 런타임 구성 변수
export BACKEND_PORT=8000
export FRONTEND_PORT=8080
export ATTACHMENT_BASE_DIR="pono_attachments"
export SHOTGRID_SERVER_URL="https://idea.shotgrid.autodesk.com"

# 데이터 베이스 설정
export DB_NAME="shotgrid_notes_db"
export DB_USER="idea"
export DB_PASSWORD="fnxmdkagh1!"
export DB_ADMIN_USER="postgres"
export DB_HOST="localhost"
export DB_PORT="5432"
export DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

