import io
import logging
import os

import requests


class LoggerWriter(io.TextIOBase):
    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.level = level
        self.telegram_token = os.getenv("TELEGRAM_TOKEN")
        self.telegram_chat = os.getenv("TELEGRAM_CHAT")

    def write(self, message: str):
        cleaned_msg = message.rstrip()
        if cleaned_msg:
            self.logger.log(self.level, cleaned_msg)
            if self.level == logging.ERROR and all([self.telegram_token, self.telegram_chat]):
                log_path = self.get_log_file_path()
                self.notify_telegram(f"Error occurred. See log file: {log_path}")
        return len(cleaned_msg)

    def flush(self):
        for handler in self.logger.handlers:
            handler.flush()

    def notify_telegram(self, message):
        api_url = f'https://api.telegram.org/bot{self.telegram_token}/sendMessage'

        try:
            response = requests.post(api_url, json={'chat_id': self.telegram_chat, 'text': message})
            response.raise_for_status()
        except Exception as error:
            self.logger.error(f"Failed to send message to Telegram: {error}")

    def get_log_file_path(self):
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                return handler.baseFilename
        return "Unknown log file"
