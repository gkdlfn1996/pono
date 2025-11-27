import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# 숨기고 싶은 로그 메시지에 포함된 문자열 목록
IGNORE_LOG_MESSAGES = [
    "connection open", # 이 줄의 주석을 해제하면 'connection open' 로그 메시지가 필터링됩니다.
    "connection closed", # 이 줄의 주석을 해제하면 'connection closed' 로그 메시지가 필터링됩니다.
    "\"WebSocket /api/notes/ws/", # 웹소켓 연결 수락 로그. 반복적인 메시지로 인해 기본적으로 필터링됩니다.
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
            "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s', # 기존 Uvicorn access 로그 포맷
        },
        "file_formatter": { # 파일에 기록될 로그 포맷 (새로 추가)
            "format": "%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "filters": {
        "endpoint_filter": {
            "()": "log_config.EndpointFilter",
        }
    },
    "handlers": { # 기존 핸들러에 파일 핸들러 추가
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
            "filters": ["endpoint_filter"],  # 콘솔 기본 핸들러에 필터 적용
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "filters": ["endpoint_filter"],  # 콘솔 접속 핸들러에 필터 적용
        },
        "app_file_handler": { # 새로 추가: 일반 앱 로그 및 Uvicorn access 로그를 파일에 기록
            "formatter": "file_formatter",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": os.path.join(os.getenv("PONO_LOG_DIR", str(Path.home() / "pono_log")), "backend_app.log"),
            "when": "midnight",  # 매일 자정마다 로그 순환
            "interval": 1,
            "backupCount": int(os.getenv("PONO_LOG_RETENTION_DAYS", "14")),  # 보관 기간 (기본 14일)
            "encoding": "utf-8",
            "filters": ["endpoint_filter"], # 파일 핸들러에도 필터 적용
        },
        "error_file_handler": { # 새로 추가: ERROR 레벨 이상의 로그만 별도 파일에 기록
            "formatter": "file_formatter",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": os.path.join(os.getenv("PONO_LOG_DIR", str(Path.home() / "pono_log")), "backend_error.log"),
            "when": "midnight",
            "interval": 1,
            "backupCount": int(os.getenv("PONO_LOG_RETENTION_DAYS", "14")),
            "encoding": "utf-8",
            "level": "ERROR", # ERROR 레벨 이상의 로그만 처리
            "filters": ["endpoint_filter"], # 파일 핸들러에도 필터 적용
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": True}, # propagate를 True로 변경
        "uvicorn.error": {"level": "INFO", "propagate": True}, # propagate를 True로 변경
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": True}, # propagate를 True로 변경
        "pono_app": { # 애플리케이션 전용 로거 (새로 추가)
            "handlers": ["app_file_handler", "error_file_handler"],
            "level": "INFO",
            "propagate": False, # uvicorn 로거와 중복 방지 (Root 로거의 propagate를 True로 설정하는 경우만 해당)
        },
    },
    "root": { # 모든 로그가 파일 핸들러를 거치도록 root 로거 설정
        "handlers": ["app_file_handler", "error_file_handler", "default"], # default 핸들러 추가: root 로거에서 콘솔로도 출력
        "level": "INFO",
    },
}
