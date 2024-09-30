import io
import os
import time
import logging

import requests


class LoggerWriter(io.TextIOBase):
    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.level = level
        self.telegram_token = os.getenv("TELEGRAM_TOKEN")
        self.telegram_chat = os.getenv("TELEGRAM_CHAT")
        self.last_telegram_notification_time = 0
        self.notification_interval = 300

    def write(self, message: str):
        cleaned_msg = message.rstrip()
        if cleaned_msg:
            self.logger.log(self.level, cleaned_msg)
            if self.level == logging.ERROR and all([self.telegram_token, self.telegram_chat]):
                current_time = time.time()
                if current_time - self.last_telegram_notification_time > self.notification_interval:
                    log_path = self.get_log_file_path()
                    self.notify_telegram(f"Error occurred. See log file: {log_path}")
                    self.last_telegram_notification_time = current_time
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
