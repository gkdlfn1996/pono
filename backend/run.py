import uvicorn
from log_config import LOGGING_CONFIG

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",          # 실행할 FastAPI 앱
        host="0.0.0.0",          # 호스트
        port=8001,               # 포트
        reload=True,             # 코드 변경 시 자동 재시작
        log_config=LOGGING_CONFIG  # 우리가 만든 커스텀 로그 설정을 직접 전달
    )
