import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Union, List, Tuple

from .gzip_rotator import GZipRotator
from .writer import LoggerWriter


def configure_logger(
    log_path: Path,
    when: str,
    interval: int,
    backupCount: int,
    logformatter: logging.Formatter,
    file_level: Union[str, int] = logging.INFO,
    rotate: bool = False,
) -> Tuple[logging.Logger, logging.Handler]:
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
    return logger, handler


def setup_logger(
    path: Path,
    when: str ='D',
    interval: int = 1,
    backupCount: int = 12,
    format: str = '%(asctime)s - %(levelname)s - %(message)s',
    rotate_main: bool = True,
    rotate_stdout: bool = False,
    rotate_error: bool = False,
    libraries: List[str] = [],
) -> logging.Logger:
    logformatter = logging.Formatter(format)

    path.mkdir(parents=True, exist_ok=True)

    main_log_path = path / "main.log"
    error_log_path = path / "error.log"
    stdout_log_path = path / "stdout.log"

    # Save the original stdout and stderr
    original_stdout = sys.stdout

    main_logger, main_handler = configure_logger(
        main_log_path, when, interval, backupCount,
        logformatter, rotate=rotate_main
    )
    stdout_logger, _ = configure_logger(
        stdout_log_path, when, interval, backupCount,
        logformatter, rotate=rotate_stdout
    )
    error_logger, _ = configure_logger(
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

    for lib_name in libraries:
        library_logger = logging.getLogger(lib_name)
        library_logger.setLevel(logging.DEBUG)
        library_logger.addHandler(main_handler)

    return main_logger
