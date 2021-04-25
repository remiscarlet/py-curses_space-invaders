#!/usr/bin/env python3

import enum


class InputType(enum.Enum):
    MOVEMENT = 0
    FIRE = 1
    QUIT = 2
    PAUSE = 3
