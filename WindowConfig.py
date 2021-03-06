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

    GAME_WON_TEXT: str = "Congratulations\nYou Win!\n\nPRESS Q TO QUIT"
    GAME_WON_DATA: List[Tuple[Tuple[int, int], str]] = []

    @staticmethod
    def getGameWonData() -> List[Tuple[Tuple[int, int], str]]:
        """
        A method instead of consts because apparently list comprehensions don't have
        variable access to class vars due to weird "comprehensions in classes" scoping oddities.

        Comprehensions because I ain't calculating that by hand for each line.

        Return shape is:
        [
            ((y1, x1), line1),
            ((y2, x2), line2),
            ((y3, x3), line3),
            etc...
        ]

        Where coords are drawpos for stdscr.addstr()
        """
        if WindowConfig.GAME_WON_DATA != []:
            return WindowConfig.GAME_WON_DATA

        lines = WindowConfig.GAME_WON_TEXT.split("\n")

        WC = WindowConfig
        game_won_data: List[Tuple[Tuple[int, int], str]] = [
            (
                (
                    WC.BORDER_WIDTH
                    + WC.TITLE_BAR_HEIGHT
                    + (Config.BOARD_HEIGHT // 2)
                    - len(lines) // 2
                    + idx,  # The 'y' of the drawpos
                    WC.TRUE_BOARD_WIDTH // 2 - len(line) // 2,  # The 'x' of the drawpos
                ),
                line,  # The text being drawn at drawpos
            )
            for idx, line in enumerate(lines)
        ]

        WindowConfig.GAME_WON_DATA = game_won_data
        return WindowConfig.GAME_WON_DATA

    SCORE_TEXT: str = "Score: "
    SCORE_TEXT_DRAW_POS: Tuple[int, int] = (
        BORDER_WIDTH + TITLE_BAR_HEIGHT + Config.BOARD_HEIGHT + BORDER_WIDTH,
        BORDER_WIDTH + 1,
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
