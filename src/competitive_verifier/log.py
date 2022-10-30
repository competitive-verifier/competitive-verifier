from logging import INFO, basicConfig

import colorlog


def configure_logging() -> None:
    log_format = "%(log_color)s%(levelname)s%(reset)s:%(name)s:%(message)s"
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(log_format))
    basicConfig(level=INFO, handlers=[handler])
