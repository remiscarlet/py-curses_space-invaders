#!/usr/bin/env python3


import curses

from typing import Dict, List, Tuple

from InputType import InputType


class InputManager:
    """
    The following describes the InputManager's behavior.

    InputManager:
        - The input manager functions by defining a series of "groups" of keys.
          These are currently:
            - "Movement keys"
            - "Fire key"
            - "Quit"
        - Retrieving the "last pressed key" in a given tick duration (ie, one update() call) is actually "get the last pressed key for group X".
            - In other words, given one tick duration there can be up to N "most recently pressed keys"
              where N is the number of input groups defined (3, for now).
        - If multiple keys are pressed in the duration of one tick, the newest pressed key will be returned
          for each group.
            - If a key in the group was not pressed, curses.ERR is returned instead.
            - Eg, assuming "wasd" are the direction keys and "space" is the fire key:
              If the keys "wd[space]" are pressed during one tick duration then the "latest pressed key"
              for the "fire" group would be the spacebar and the key for the "movement" group would be "d" while
              the "quit" group would return curses.ERR.
    """

    stdscr: curses.window  # type: ignore

    """
    Do we still need the buffer functionality? Might not need it depending on execution flow in SpaceInvaders.run()
    """
    buffer_cleared: Dict[InputType, bool] = {
        InputType.MOVEMENT: False,
        InputType.FIRE: False,
        InputType.QUIT: False,
        InputType.PAUSE: False,
    }

    last_pressed: Dict[InputType, int] = {
        InputType.MOVEMENT: curses.ERR,
        InputType.FIRE: curses.ERR,
        InputType.QUIT: curses.ERR,
        InputType.PAUSE: curses.ERR,
    }

    groups: Dict[InputType, List[int]] = {
        InputType.MOVEMENT: [curses.KEY_LEFT, ord("a"), curses.KEY_RIGHT, ord("d")],
        InputType.FIRE: [ord(" ")],
        InputType.QUIT: [ord("q")],
        InputType.PAUSE: [ord("p")],
    }

    reverse_group_lookup: Dict[int, InputType] = {}

    def __init__(self, stdscr: curses.window) -> None:  # type: ignore
        self.stdscr = stdscr

        for input_type, keys in self.groups.items():
            for key in keys:
                self.reverse_group_lookup[key] = input_type

    def shouldQuit(self) -> bool:
        last_pressed_key_for_quit = self.getLastPressedKeyForGroup(
            InputType.QUIT, False
        )
        return last_pressed_key_for_quit == ord("q")

    def storeInput(self) -> None:
        key = self.stdscr.getch()

        # If curses.ERR, no key was pressed.
        while key != curses.ERR:
            if key in self.reverse_group_lookup:
                # If the key pressed is not a key defined in our InputManager,
                # ignore and get next buffered key
                group = self.reverse_group_lookup[key]
                self.last_pressed[group] = key
                self.buffer_cleared[group] = False

            key = self.stdscr.getch()

    def getLastPressedKeyForGroup(
        self, input_type: InputType, clear_buffer: bool = True
    ) -> int:
        if self.buffer_cleared[input_type]:
            return curses.ERR
        else:
            key = self.last_pressed[input_type]

            if clear_buffer:
                self.buffer_cleared[input_type] = True
            return key
