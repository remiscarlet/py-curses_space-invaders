#!/usr/bin/env python3

from Colors import Colors
from Entity import Entity
from EntityType import EntityType


class Borders:
    VERTICAL = Entity("║", Colors.WHITE, EntityType.BORDER)
    HORIZONTAL = Entity("═", Colors.WHITE, EntityType.BORDER)
    TOP_LEFT = Entity("╔", Colors.WHITE, EntityType.BORDER)
    TOP_RIGHT = Entity("╗", Colors.WHITE, EntityType.BORDER)
    BOT_LEFT = Entity("╚", Colors.WHITE, EntityType.BORDER)
    BOT_RIGHT = Entity("╝", Colors.WHITE, EntityType.BORDER)
    INTERSECT_LEFT = Entity("╠", Colors.WHITE, EntityType.BORDER)
    INTERSECT_RIGHT = Entity("╣", Colors.WHITE, EntityType.BORDER)
