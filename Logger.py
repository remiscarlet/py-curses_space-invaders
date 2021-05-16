#!/usr/bin/env python3

import logging

from Config import Config


class Logger:
    logger: logging.Logger

    def __init__(self):
        logger = logging.getLogger("SpaceInvaders")
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s")

        file_handler = logging.FileHandler(Config.LOG_PATH)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        Logger.logger = logger

    @staticmethod
    def info(msg: str):
        Logger.logger.info(msg)

    @staticmethod
    def debug(msg: str):
        Logger.logger.debug(msg)


Logger()
