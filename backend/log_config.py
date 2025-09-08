import logging

# 숨기고 싶은 로그 메시지에 포함된 문자열 목록
IGNORE_LOG_MESSAGES = [
    "connection open",
    "connection closed",
    "\"WebSocket /api/notes/ws/", # 웹소켓 연결 수락 로그
]

class EndpointFilter(logging.Filter):
    """
    특정 로그 메시지를 무시하는 커스텀 필터 클래스입니다.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        log_message = record.getMessage()
        
        is_ignored = False
        # 숨길 메시지 목록을 하나씩 순회합니다.
        for msg in IGNORE_LOG_MESSAGES:
            # 현재 로그 메시지 안에 숨기고 싶은 문자열(msg)이 포함되어 있다면,
            if msg in log_message:
                is_ignored = True  # 무시해야 할 로그라고 표시하고,
                break              # 더 이상 검사할 필요가 없으므로 반복을 중단합니다.
        
        # 무시해야 할 로그이면 False를, 아니면 True를 반환합니다.
        return not is_ignored

# Uvicorn에 적용할 로깅 설정 딕셔너리
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
        },
    },
    "filters": {
        "endpoint_filter": {
            "()": "log_config.EndpointFilter",
        }
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
            "filters": ["endpoint_filter"],  # 기본 핸들러에 필터 적용
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "filters": ["endpoint_filter"],  # 접속 핸들러에 필터 적용
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}
