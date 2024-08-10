import logging

import colorlog

from .IntraAPIClient import IntraAPIClient
from .Token import Token
from .utils import APIVersion

stderr = colorlog.StreamHandler()
formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s [%(levelname)8.8s] - %(module)10.10s.%(funcName)-15.15s  ||  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    reset=True,
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    },
    secondary_log_colors={},
)

stderr.setFormatter(formatter)
logger = colorlog.getLogger(__name__)
logger.addHandler(stderr)
logger.setLevel(logging.WARNING)
