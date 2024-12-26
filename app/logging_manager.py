import logging
from logging.config import dictConfig
from logging_config import LOGGING_CONFIG

class LoggerManager:
    """전역적으로 사용할 로깅 관리 클래스"""
    def __init__(self, logger_name="app"):
        # 로깅 설정 초기화
        dictConfig(LOGGING_CONFIG)
        self.logger = logging.getLogger(logger_name)

    def debug(self, message, *args, **kwargs):
        self.logger.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        self.logger.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self.logger.error(message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        self.logger.critical(message, *args, **kwargs)


# 전역적으로 사용할 로거 인스턴스
logger = LoggerManager()