import sys
import logging
import logging.handlers
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Union, Type
from dataclasses import dataclass
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler

from .gzip_rotator import GZipRotator
from .writer import LoggerWriter


@dataclass
class StreamConfig:
    rotate: bool
    redirect: bool
    log_level: int = logging.INFO


@dataclass
class StreamResponse:
    logger: logging.Logger
    handler: logging.Handler


def configure_logger(
    log_path: Path,
    logformatter: logging.Formatter,
    log_level: int = logging.INFO,
    rotate: bool = False,
    rotate_handler: Optional[Union[TimedRotatingFileHandler, RotatingFileHandler]] = None,
) -> Tuple[logging.Logger, logging.Handler]:
    logger = logging.getLogger(log_path.stem)
    logger.setLevel(log_level)
    
    if rotate and rotate_handler:
        handler = rotate_handler
        handler.rotator = GZipRotator(is_size_rotation=isinstance(rotate_handler, RotatingFileHandler))
    else:
        handler = logging.FileHandler(log_path)

    handler.setLevel(log_level)
    handler.setFormatter(logformatter)
    logger.addHandler(handler)
    
    logger.propagate = False  # Avoid double logging
    return logger, handler


def setup_logger(
    path: Path,
    format: str = '%(asctime)s - %(levelname)s - %(message)s',
    rotate_handler: Optional[Union[Type[TimedRotatingFileHandler], Type[RotatingFileHandler]]] = None,
    rotate_handler_kwargs: Dict = {
        'when': 'D',
        'interval': 1,
        'backupCount': 12,
    },
    stream_configs: Dict[str, StreamConfig] = {
        'main': StreamConfig(rotate=True, redirect=True, log_level=logging.INFO),
        'stdout': StreamConfig(rotate=False, redirect=True, log_level=logging.INFO),
        'stderr': StreamConfig(rotate=False, redirect=True, log_level=logging.ERROR),
    },
    libraries: List[str] = [],
) -> Dict[str, StreamResponse]:
    if not any([stream_config.redirect for stream_config in stream_configs.values()]):
        raise ValueError("At least one stream must be redirected")

    logformatter = logging.Formatter(format)
    path.mkdir(parents=True, exist_ok=True)

    # Save the original stdout and stderr
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    streams = dict()
    level_map = {"stdout": logging.INFO, "stderr": logging.ERROR}

    for stream_name, stream_config in stream_configs.items():
        if stream_config.redirect:
            log_path = path / f"{stream_name}.log"
            rotate_handler_instance = rotate_handler(log_path, **rotate_handler_kwargs) if callable(rotate_handler) else None
            logger, handler = configure_logger(
                log_path,
                logformatter,
                log_level=stream_config.log_level,
                rotate=stream_config.rotate,
                rotate_handler=rotate_handler_instance
            )
            streams[stream_name] = StreamResponse(logger, handler)
            if stream_name in {"stdout", "stderr"}:
                setattr(sys, stream_name, LoggerWriter(logger, level_map[stream_name]))

    # Add a StreamHandler to log to the console
    console_handler = logging.StreamHandler(original_stdout)
    console_handler.setLevel(logging.INFO)  # Set level to INFO for console output
    console_handler.setFormatter(logformatter)
    if "main" in streams:
        streams["main"].logger.addHandler(console_handler)

    for lib_name in libraries:
        library_logger = logging.getLogger(lib_name)
        library_logger.setLevel(logging.DEBUG)
        if "main" in streams:
            library_logger.addHandler(streams["main"].handler)

    return streams
