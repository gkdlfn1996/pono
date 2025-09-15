import uvicorn
import os
from pathlib import Path
from log_config import LOGGING_CONFIG

if __name__ == "__main__":
    # 홈 디렉토리를 기준으로 첨부파일 '기본' 저장 경로를 정의
    attachment_base_path = Path.home() / 'pono_attachments'
    # 서버 시작 전, 첨부파일 기본 디렉토리가 없으면 생성
    print(f"Ensuring attachment base directory exists: {attachment_base_path}")
    os.makedirs(attachment_base_path, exist_ok=True)

    uvicorn.run(
        "app.main:app",          # 실행할 FastAPI 앱
        host="0.0.0.0",          # 호스트
        port=8001,               # 포트
        reload=True,             # 코드 변경 시 자동 재시작
        log_config=LOGGING_CONFIG  # 우리가 만든 커스텀 로그 설정을 직접 전달
    )