#!/usr/bin/env python3

###########
# Configs #
###########


class Config:
    BOARD_HEIGHT: int = 15
    BOARD_WIDTH: int = 25
    ENEMY_COUNT: int = BOARD_WIDTH * 2
    ENEMY_SPACING: int = 2
    TICKS_PER_SECOND: int = 10

    TICKS_PER_ENEMY_MOVEMENT: int = 3

    LOG_PATH: str = "it.was.aliens.log"
