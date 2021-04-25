#!/usr/bin/env python3

import itertools

from typing import Tuple, List

from Config import Config


class WindowConfig:
    """
    This class houses consts related to "window" sizes - ie cell width/lengths
    for various components of the UI.

    Layout:
    -------------  <-|-- BORDER_WIDTH
    | TITLE BAR |     |
    |-----------|   <-|-- TITLE_BAR_HEIGHT
    |           |      |
    |   GAME    |      |
    |  WINDOW   |      |
    |           |    <-|-- BOARD_HEIGHT # BOARD_HEIGHT does _not_ include the bottom border size due to it being the game board on the inside of borders.
    |-----------|     <-|-- BORDER_WIDTH
    | STATS BAR |        |
    -------------      <-|-- PLAYER_STATS_HEIGHT
    """

    BORDER_WIDTH: int = (
        1  # Eh... please don't change this for now. Multi-cell width borders are blegh.
    )

    TITLE_BAR_HEIGHT: int = 1 + BORDER_WIDTH  # 1 row for title + border width
    PLAYER_STATS_HEIGHT: int = 1 + BORDER_WIDTH  # 1 row for all stats + border width

    OFFSET_ROWS_TO_DRAW_HORIZONTAL: List[int] = [
        0,
        TITLE_BAR_HEIGHT,
        Config.BOARD_HEIGHT + BORDER_WIDTH,
        PLAYER_STATS_HEIGHT,
    ]

    TRUE_BOARD_WIDTH: int = Config.BOARD_WIDTH + 2 * BORDER_WIDTH
    TRUE_BOARD_HEIGHT: int = (
        sum(OFFSET_ROWS_TO_DRAW_HORIZONTAL) + 1
    )  # +1 because offset vs array length

    WINDOW_TITLE: str = "Space Invaders!"
    WINDOW_TITLE_DRAW_POS: Tuple[int, int] = (
        BORDER_WIDTH,
        TRUE_BOARD_WIDTH // 2 - len(WINDOW_TITLE) // 2,
    )  # (y, x)

    PAUSED_TEXT: str = "PAUSED"
    PAUSED_TEXT_DRAW_POS: Tuple[int, int] = (
        BORDER_WIDTH + TITLE_BAR_HEIGHT + (Config.BOARD_HEIGHT // 2),
        TRUE_BOARD_WIDTH // 2 - len(PAUSED_TEXT) // 2,
    )

    @staticmethod
    def getRowsToDrawHorizontals() -> List[int]:
        rows = list(itertools.accumulate(WindowConfig.OFFSET_ROWS_TO_DRAW_HORIZONTAL))
        assert (
            rows[-1] == WindowConfig.TRUE_BOARD_HEIGHT - 1
        )  # Ensure our offsets and true board height match.
        return rows

    @staticmethod
    def convertToTrueY(y: int) -> int:
        return WindowConfig.TITLE_BAR_HEIGHT + WindowConfig.BORDER_WIDTH + y

    @staticmethod
    def convertToTrueX(x: int) -> int:
        return WindowConfig.BORDER_WIDTH + x
