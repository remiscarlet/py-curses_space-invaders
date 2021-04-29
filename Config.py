#!/usr/bin/env python3

###########
# Configs #
###########

from Colors import Colors

from typing import List


class Config:
    BOARD_HEIGHT: int = 15
    BOARD_WIDTH: int = 25
    ENEMY_COUNT: int = BOARD_WIDTH * 2
    ENEMY_SPACING: int = 2
    TICKS_PER_SECOND: int = 10

    TICKS_PER_ENEMY_MOVEMENT: int = 3

    LOG_PATH: str = "it.was.aliens.log"

    TICKS_PER_SHOT: int = 0

    # PLAYER_SYMBOL: str = "♕"
    PLAYER_SYMBOL: str = "ﾑ"
    PLAYER_SYMBOL_FALLBACK: str = "P"
    PLAYER_COLOR: int = Colors.RED

    # ENEMY_SYMBOL: str = "☠"
    # ENEMY_SYMBOL: str = "ｪ"
    ENEMY_SYMBOL: str = "◦"
    ENEMY_SYMBOL_FALLBACK: str = "A"
    ENEMY_COLORS: List[int] = [
        Colors.GREEN,
        Colors.YELLOW,
        Colors.CYAN,
        Colors.MAGENTA,
    ]
