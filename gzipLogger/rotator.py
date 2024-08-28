import io
import os
import gzip
import sys
import logging
import logging.handlers
from pathlib import Path


class GZipRotator:
    def __call__(self, source, dest):
        try:
            os.rename(source, dest)
            with open(dest, 'rb') as f_in:
                with gzip.open(f"{dest}.gz", 'wb') as f_out:
                    f_out.writelines(f_in)
        except Exception as e:
            logging.error(f"Error compressing log file: {e}")
        finally:
            if os.path.exists(dest):
                try:
                    os.remove(dest)
                except Exception as e:
                    logging.error(f"Error deleting log file: {e}")


class LoggerWriter(io.TextIOBase):
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message.rstrip():
            self.logger.log(self.level, message.rstrip())

    def flush(self):
        for handler in self.logger.handlers:
            handler.flush()


def configure_logger(
    log_path,
    when,
    interval,
    backupCount,
    logformatter,
    file_level=logging.INFO,
    rotate=False,
):
    logger = logging.getLogger(log_path.stem)
    logger.setLevel(file_level)
    
    if rotate:
        handler = logging.handlers.TimedRotatingFileHandler(filename=log_path, when=when, interval=interval, backupCount=backupCount)
        handler.rotator = GZipRotator()
    else:
        handler = logging.FileHandler(log_path)

    handler.setLevel(file_level)
    handler.setFormatter(logformatter)
    logger.addHandler(handler)
    
    logger.propagate = False  # Avoid double logging
    return logger


def setup_logger(
    path: Path,
    when='D',
    interval=1,
    backupCount=12,
    format='%(asctime)s - %(levelname)s - %(message)s',
    rotate_main=True,
    rotate_stdout=False,
    rotate_error=False
):
    logformatter = logging.Formatter(format)

    path.mkdir(parents=True, exist_ok=True)

    main_log_path = path / "main.log"
    error_log_path = path / "error.log"
    stdout_log_path = path / "stdout.log"

    # Save the original stdout and stderr
    original_stdout = sys.stdout

    main_logger = configure_logger(
        main_log_path, when, interval, backupCount,
        logformatter, rotate=rotate_main
    )
    stdout_logger = configure_logger(
        stdout_log_path, when, interval, backupCount,
        logformatter, rotate=rotate_stdout
    )
    error_logger = configure_logger(
        error_log_path, when, interval, backupCount,
        logformatter, file_level=logging.ERROR, rotate=rotate_error
    )

    # Redirect stdout and stderr to logger
    sys.stdout = LoggerWriter(stdout_logger, logging.INFO)
    sys.stderr = LoggerWriter(error_logger, logging.ERROR)

    # Add a StreamHandler to log to the console
    console_handler = logging.StreamHandler(original_stdout)
    console_handler.setLevel(logging.INFO)  # Set level to INFO for console output
    console_handler.setFormatter(logformatter)
    main_logger.addHandler(console_handler)

    return main_logger