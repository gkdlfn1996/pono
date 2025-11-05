#!/bin/bash
set -e

# ===== 경로/버전 (이 파일 내부에서만 관리) =====
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." &> /dev/null && pwd )"

PY_VER="3.10.13"
PY_PREFIX="$PROJECT_ROOT/.python/python-$PY_VER"    # 최종 설치 루트
PY_BIN="$PY_PREFIX/bin/python3.10"                  # 최종 실행 파일
SRC_DIR="$PROJECT_ROOT/.python/src"                 # 소스/빌드 위치
TGZ_PATH="$SRC_DIR/Python-$PY_VER.tgz"              # 내려받을 아카이브
TGZ_URL="https://www.python.org/ftp/python/$PY_VER/Python-$PY_VER.tgz"

# 0) 이미 설치돼 있으면 그대로 사용
if [ -x "$PY_BIN" ]; then
  echo "$PY_BIN"
  exit 0
fi

echo "파이썬 $PY_VER 설치를 시작합니다."

# 1) 소스 아카이브 준비
mkdir -p "$SRC_DIR"
if [ ! -f "$TGZ_PATH" ]; then
  curl -fL "$TGZ_URL" -o "$TGZ_PATH"
fi

# 2) 압축 해제
tar -C "$SRC_DIR" -xf "$TGZ_PATH"

if [ -d "$SRC_DIR/Python-$PY_VER" ]; then
  cd "$SRC_DIR/Python-$PY_VER"
else
  echo "소스 디렉토리를 찾을 수 없습니다: $SRC_DIR/Python-$PY_VER" 1>&2
  exit 1
fi

echo "파이썬 소스 tgz 다운로드 및 압축 해제 완료"

# 3) 빌드/설치
mkdir -p "$PY_PREFIX"
./configure --prefix="$PY_PREFIX"

echo "---------------파이썬 빌드를 시작합니다.-------------------"

make -j"$(nproc)"
make install

# 4) 검증 및 결과 출력
if [ ! -x "$PY_BIN" ]; then
  echo "내부 Python 설치에 실패했습니다." 1>&2
  exit 1
fi

MAJ_MIN="$("$PY_BIN" -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')"
if [ "$MAJ_MIN" != "3.10" ]; then
  echo "설치된 Python 버전이 3.10이 아닙니다: $MAJ_MIN" 1>&2
  exit 1
fi

echo "---------------파이썬 빌드가 완료되었습니다.-------------------"

echo "$PY_BIN"

