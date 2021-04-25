#!/usr/bin/env python3
from __future__ import annotations

import copy
import enum
import time
import curses
import random
import logging
import itertools

from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple


from Logger import Logger
from Config import Config
from Colors import Colors
from WindowConfig import WindowConfig
from Board import Board
from Entity import Entity
from EntityType import EntityType
from InputManager import InputManager
from InputType import InputType

"""
What Is:
    - Space Invaders implemented with curses and Python 3.7+

What For:
    - Pair Programming Task for applying to the Recurse Center

Currently Does:
    - Configurable board size
    - Configurable enemy count
    - Configurable tick length
    - Border on game board
    - Quitting ('Q')
    - Pausing ('P')
    - Player Movement ('A'/'L_ARROW' or 'D'/'R_ARROW')
    - Enemy Movement (Snakes down from top to bot)
    - Title/Pause Text
    - Colors

Features To Implement:
    - Shooting/Destroying enemies
    - Score

Notes/Assumptions:
    - Will error out if screen size is smaller than grid size
    - If screen size is large than grid size, will display the grid anchored to upper left corner.

Known "Bugs":
    - If you hold a key configured with InputManager, initial keypress is recognized, then
      the key is seen as "released", but then will correctly detect it as being "held" again soon thereafter.
        - Wait, this is probably just my OS's key repeat delay and not the code...
        - Oh, that's probably why proper input managers use lower level libraries and not literally keystrokes...
"""

# Classes


class SpaceInvaders:
    """
    Main game controller.

    Handles game loop, updating game entities, and drawing everything with curses.
    """

    stdscr: curses.window  # type: ignore

    player: Entity
    enemies: List[Entity]

    player_pos: Tuple[int, int]

    is_paused: bool = False

    SHOOT_TICK: int = 1  # Number of ticks for "bullet" to travel forward one cell
    SHOOT_DELAY: int = 2  # Can shoot once every SHOOT_DELAY ticks.

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

    def __init__(self, _stdscr: curses.window) -> None:  # type: ignore
        """
        We have to do a weird thing here cuz colors can't be initialized
        without curses.initscr() being called first.
        """

        Colors()

        self.stdscr = _stdscr
        self.stdscr.keypad(True)
        self.stdscr.nodelay(True)

        curses.start_color()
        curses.use_default_colors()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(False)

        self.inputManager = InputManager(self.stdscr)

        self.ensureScreenLargeEnough()
        self.initializeEntities()

        self.board = Board(self.player, self.enemies, Config.ENEMY_COUNT)

    def __del__(self) -> None:
        self.stdscr.keypad(False)

        curses.nocbreak()
        curses.echo()
        curses.endwin()
        curses.curs_set(True)

    def ensureScreenLargeEnough(self) -> None:
        """
        Maybe can just throw in __init__()?
        """
        if curses.LINES < Config.BOARD_HEIGHT or curses.COLS < Config.BOARD_WIDTH:
            raise Exception(
                f"Screen is not large enough. Please increase so there is a minimum of {Config.BOARD_WIDTH} x {Config.BOARD_HEIGHT}"
            )

    def initializeEntities(self) -> None:
        """
        Ehh... Kinda unnecessary rn
        TODO: Check for fallback chars - ie cannot display unicode? Maybe hard cuz clientside rendering? Args?
        """

        self.player = Entities.PLAYER
        self.enemies = Entities.ENEMIES

    #######################
    # Game Loop Functions #
    #######################

    def run(self) -> None:
        """
        NOTE:
            This is a _naive_ implementation of "ticks" or general time keeping.

            There are definitely more robust ways to do this, but this should be sufficient for now.
        """

        def new_tick_start() -> bool:
            return target_tick_dur_ns < time.time_ns() - curr_tick_start_ns

        # ns -> nanoseconds
        target_tick_dur_ns = 1 * 1000 * 1000 * 1000 / Config.TICKS_PER_SECOND
        curr_tick_start_ns = time.time_ns()

        while True:
            self.inputManager.storeInput()

            if self.inputManager.shouldQuit():
                break

            if new_tick_start():
                curr_tick_start_ns = time.time_ns()

                self.update()
                self.draw()

    def updatePlayer(self, pressed_key: int) -> None:
        if pressed_key in (curses.KEY_LEFT, ord("a")) and self.player.canMoveLeft():
            Logger.info("Moving ship to the left")
            self.player.moveLeft(self.board)
        elif pressed_key in (curses.KEY_RIGHT, ord("d")) and self.player.canMoveRight():
            Logger.info("Moving ship to the right")
            self.player.moveRight(self.board)

    def updateEnemies(self) -> None:
        for enemy in reversed(self.board.getAliveEnemies()):
            enemy.moveToNextPos(self.board)

    def togglePause(self) -> None:
        self.is_paused = not self.is_paused

    def update(self) -> None:
        Logger.info("Input:")
        for group in InputType:
            pressed_key = self.inputManager.getLastPressedKeyForGroup(group)
            Logger.info(f"{InputType(group).name}: {pressed_key}")

            if pressed_key == curses.ERR:
                # No input. Check next group.
                continue

            if group == InputType.PAUSE:
                self.togglePause()

            if not self.is_paused and group in (InputType.MOVEMENT, InputType.FIRE):
                self.updatePlayer(pressed_key)

        if not self.is_paused:
            self.updateEnemies()

    def draw(self) -> None:
        if not self.is_paused:
            self.drawGameEntities()
        else:
            self.drawPauseScreen()

        self.drawText()

        self.stdscr.refresh()

    def drawGameEntities(self) -> None:
        for y, row_data in enumerate(self.board.getBoard()):
            for x, entity in enumerate(row_data):
                if entity is not None:
                    self.stdscr.addch(y, x, entity.symbol, Colors.getAttr(entity.color))
                else:
                    self.stdscr.addch(y, x, " ")

    def drawPauseScreen(self) -> None:
        text_y, text_x = WindowConfig.PAUSED_TEXT_DRAW_POS
        self.stdscr.addstr(text_y, text_x, WindowConfig.PAUSED_TEXT)

    def drawText(self) -> None:
        title_y, title_x = WindowConfig.WINDOW_TITLE_DRAW_POS
        self.stdscr.addstr(title_y, title_x, WindowConfig.WINDOW_TITLE)

        # TODO: Implement score and draw score here.


class Entities:
    # TODO: Implement player and enemy projectiles.
    PLAYER: Entity = Entity(
        SpaceInvaders.PLAYER_SYMBOL, SpaceInvaders.PLAYER_COLOR, EntityType.PLAYER
    )
    ENEMIES: List[Entity] = [
        Entity(SpaceInvaders.ENEMY_SYMBOL, color, EntityType.ENEMY)
        for color in SpaceInvaders.ENEMY_COLORS
    ]


###############
# Entry Point #
###############


def main(stdscr: curses.window) -> None:  # type: ignore
    game = SpaceInvaders(stdscr)
    game.run()
    del game


if __name__ == "__main__":
    curses.wrapper(main)
