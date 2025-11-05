#!/bin/bash
set -e

# 공통 설정을 로드하여 PY_BIN, PY_VER 등의 변수를 가져옴
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." &> /dev/null && pwd )"
source "$PROJECT_ROOT/config.sh"

# 0) 이미 설치돼 있으면 그대로 사용
if [ -x "$PY_BIN" ]; then
  echo "$PY_BIN"
  exit 0
fi

echo "파이썬 $PY_VER 설치를 시작합니다." >&2

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

echo "파이썬 소스 tgz 다운로드 및 압축 해제 완료" >&2

# 3) 빌드/설치
mkdir -p "$PY_PREFIX"
./configure --prefix="$PY_PREFIX"

echo "---------------파이썬 빌드를 시작합니다.-------------------" >&2

make -j"$(nproc)"
make install

# 4) 검증 및 결과 출력
if [ ! -x "$PY_BIN" ]; then
  echo "내부 Python 설치에 실패했습니다." 1>&2
  exit 1
fi

MAJ_MIN_VER=$(echo "$PY_VER" | cut -d. -f1,2)
if ! "$PY_BIN" -c "import sys; assert sys.version_info[:2] == tuple(map(int, '$MAJ_MIN_VER'.split('.')))"; then
  echo "설치된 Python 버전이 $MAJ_MIN_VER 이 아닙니다." 1>&2
  exit 1
fi

echo "---------------파이썬 빌드가 완료되었습니다.-------------------" >&2
echo "$PY_BIN"


