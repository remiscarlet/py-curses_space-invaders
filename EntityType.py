#!/usr/bin/env python3

import enum


class EntityType(enum.Enum):
    PLAYER = 0
    PLAYER_PROJECTILE = 1
    ENEMY = 2
    ENEMY_PROJECTILE = 3
    OBSTACLE = 4
    BORDER = 5
