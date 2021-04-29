#!/usr/bin/env python3


from Config import Config
from Entity import Entity
from EntityType import EntityType

from typing import List


class Entities:
    @staticmethod
    def genNewPlayerProjectile():
        return Entity("|", Config.PLAYER_COLOR, EntityType.PLAYER_PROJECTILE)

    # TODO: Implement player and enemy projectiles.
    PLAYER: Entity = Entity(
        Config.PLAYER_SYMBOL, Config.PLAYER_COLOR, EntityType.PLAYER
    )
    ENEMIES: List[Entity] = [
        Entity(Config.ENEMY_SYMBOL, color, EntityType.ENEMY)
        for color in Config.ENEMY_COLORS
    ]
