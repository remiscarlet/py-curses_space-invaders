#!/usr/bin/env python3

import curses

from typing import Dict


class Colors:
    """
    Implements curses color helpers

    Due to needing to initialize colors after the call to curses.initscr(), we
    initialize Colors() for the first time in SpaceInvaders.__init__(). This is because
    we use curses.wrapper() meaning we can't actually call curses.init_pair()
    until SpaceInvaders() has also been initialized (through curses.wrapper())
    """

    RED: int = 1
    GREEN: int = 2
    YELLOW: int = 3
    CYAN: int = 4
    MAGENTA: int = 5
    WHITE: int = 6

    mapping: Dict[
        int, int
    ] = {}  # The value 'int' is a curses attribute which is an int bitmask

    def __init__(self) -> None:
        curses.init_pair(self.RED, curses.COLOR_RED, curses.COLOR_BLACK)
        Colors.mapping[self.RED] = curses.color_pair(self.RED)

        curses.init_pair(self.GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
        Colors.mapping[self.GREEN] = curses.color_pair(self.GREEN)

        curses.init_pair(self.YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        Colors.mapping[self.YELLOW] = curses.color_pair(self.YELLOW)

        curses.init_pair(self.CYAN, curses.COLOR_CYAN, curses.COLOR_BLACK)
        Colors.mapping[self.CYAN] = curses.color_pair(self.CYAN)

        curses.init_pair(self.MAGENTA, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        Colors.mapping[self.MAGENTA] = curses.color_pair(self.MAGENTA)

        curses.init_pair(self.WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
        Colors.mapping[self.WHITE] = curses.color_pair(self.WHITE)

    @staticmethod
    def getAttr(color_id: int) -> int:
        if color_id not in Colors.mapping:
            raise Exception(f"Got a color ID that we haven't mapped! Got: {color_id}")
        return Colors.mapping[color_id]
