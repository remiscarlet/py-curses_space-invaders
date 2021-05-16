#!/usr/bin/env python3
from __future__ import annotations

import copy
import random

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    # We only need to import these for type checking purposes as we only use it
    # for type hinting in func signatures. Can't normally include or it causes
    # circular import errors
    from SpaceInvaders import SpaceInvaders


from Colors import Colors
from Config import Config
from Entity import Entity
from EntityType import EntityType
from Entities import Entities
from WindowConfig import WindowConfig
from Logger import Logger
from Borders import Borders


class Board:
    """
    Handles board state. The board is differentiated from the larger "window" or screen
    by the fact that Board() only handles the gameplay area of the window.

    As such all coordinates assume game coordinates and NOT the "true" coordinates
    that curses use in functions like stdscr.getch()

    Translation from game coords to "true" coords is handled with WindowConfig.convertToTrueY() and *TrueX()
    """

    curr_board: List[List[List[Entity]]]
    next_board: List[List[List[Entity]]]
    empty_board: List[List[List[Entity]]]

    instances: Dict[EntityType, List[Entity]] = {}

    def __init__(
        self,
        player: Entity,
        enemies: List[Entity],
        num_enemies: int,
        space_invaders: "SpaceInvaders",
    ) -> None:
        for entity_type in EntityType:
            Logger.info(str(entity_type))
            self.instances[entity_type] = []

        self.__initializeBoard()
        self.__populateBoard(player, enemies, num_enemies)
        self.space_invaders = space_invaders

    def finalizePosUpdates(self) -> None:
        self.clearCollisions()
        self.curr_board = copy.deepcopy(self.next_board)
        self.next_board = copy.deepcopy(self.empty_board)

    def clearCollisions(self) -> None:
        for y, row_data in enumerate(self.getBoard(get_next_board=True)):
            for x, entities in enumerate(row_data):
                if len(entities) < 2:
                    continue
                elif len(entities) > 2:
                    Logger.info(f"{entities}")
                    raise Exception(
                        "Should not ever have more than two entities on one position!"
                    )

                Logger.info(f"Detected collision at: (true_y:{y}, true_x:{x})")
                Logger.info(f"{entities}")
                for ent in entities:
                    if ent.entity_type == EntityType.ENEMY:
                        self.incrementScore()
                    Logger.info(f"{ent}")
                    self.clearPosAndEntity(ent)

    def clearPosAndEntity(self, ent: Entity) -> None:
        Logger.info(f"Clearing: {ent}")

        y, x = ent.position
        self.setEntityAtPos(y, x, None)
        self.deleteEntityReferences(ent)

    def incrementScore(self) -> None:
        self.space_invaders.incrementScore()

    def __initializeBoard(self) -> None:
        """
        Initialize the board with empty cells and draw border
        """
        empty_board: List[List[List[Entity]]] = [
            [[] for _ in range(WindowConfig.TRUE_BOARD_WIDTH)]
            for _ in range(WindowConfig.TRUE_BOARD_HEIGHT)
        ]

        assert WindowConfig.BORDER_WIDTH == 1  # Pls no multi-width borders...

        rows_to_draw: List[int] = WindowConfig.getRowsToDrawHorizontals()

        # Non-corner Vertical borders
        right_border_x = WindowConfig.TRUE_BOARD_WIDTH - 1
        for y in range(1, WindowConfig.TRUE_BOARD_HEIGHT - 1):
            if (
                y in rows_to_draw[1:-1]
            ):  # Bounds check? 0th and last rows use corner chars - not intersections
                # Draw an intersection
                empty_board[y][0].append(Borders.INTERSECT_LEFT)
                empty_board[y][right_border_x].append(Borders.INTERSECT_RIGHT)
            else:
                # Draw a vertical line
                empty_board[y][0].append(Borders.VERTICAL)
                empty_board[y][right_border_x].append(Borders.VERTICAL)

        # Non-corner Horizontal borders
        for x in range(1, WindowConfig.TRUE_BOARD_WIDTH - 1):
            for y in rows_to_draw:
                empty_board[y][x].append(Borders.HORIZONTAL)

        # Corners
        max_x = WindowConfig.TRUE_BOARD_WIDTH - 1
        max_y = WindowConfig.TRUE_BOARD_HEIGHT - 1
        empty_board[0][0].append(Borders.TOP_LEFT)
        empty_board[0][max_x].append(Borders.TOP_RIGHT)
        empty_board[max_y][0].append(Borders.BOT_LEFT)
        empty_board[max_y][max_x].append(Borders.BOT_RIGHT)

        self.empty_board = empty_board
        self.curr_board = copy.deepcopy(self.empty_board)
        self.next_board = copy.deepcopy(self.empty_board)

    def __populateBoard(
        self, player: Entity, enemies: List[Entity], num_enemies: int
    ) -> None:
        """
        Place entities on the board
        - Player
        - Enemies
        - TODO: Obstacles
        """

        # Place player
        player_y = Config.BOARD_HEIGHT - 1
        player_x = Config.BOARD_WIDTH // 2
        self.setEntityAtPos(player_y, player_x, player, use_curr_board=True)

        enemy_y, enemy_x = 0, 0
        for i in range(num_enemies):
            enemy = copy.deepcopy(
                random.choice(enemies)
            )  # Deep copy to ensure no shared refs

            self.setEntityAtPos(enemy_y, enemy_x, enemy, use_curr_board=True)

            dy, dx = enemy.genNextPosOffset(enemy_y, enemy_x, Config.ENEMY_SPACING)
            enemy_y += dy
            enemy_x += dx

            self.instances[EntityType.ENEMY].append(enemy)

        Logger.info("===== Done populating initial entity positions.")

    def spawnProjectile(
        self, entity_pos: Tuple[int, int], is_player_projectile: bool
    ) -> None:
        if is_player_projectile:
            offset_y, offset_x = (-1, 0)
        else:
            offset_y, offset_x = (+1, 0)
        entity_y, entity_x = entity_pos
        proj_y, proj_x = entity_y + offset_y, entity_x + offset_x

        projectile = Entities.genNewPlayerProjectile()
        self.setEntityAtPos(proj_y, proj_x, projectile)

        entity_type = (
            EntityType.PLAYER_PROJECTILE
            if is_player_projectile
            else EntityType.ENEMY_PROJECTILE
        )
        self.instances[entity_type].append(projectile)
        Logger.info(
            f"Spawning projectile: {projectile} - is_player: {is_player_projectile}"
        )

    def getBoard(self, get_next_board=False) -> List[List[List[Entity]]]:
        return self.next_board if get_next_board else self.curr_board

    def drawBoard(
        self,
        stdscr: Optional[curses.window] = None,  # type: ignore
        return_as_str: bool = False,
    ) -> Optional[str]:
        return_str: Optional[str] = None

        for y, row_data in enumerate(self.getBoard()):
            for x, entities in enumerate(row_data):
                if len(entities) > 1:
                    raise Exception(
                        "Got to draw step without clearing out multi-entity cells. Should be cleared by collision handlers"
                    )
                entity = entities[0] if len(entities) == 1 else None
                if entity is not None:
                    if return_as_str:
                        if return_str is None:
                            return_str = ""
                        return_str += entity.symbol
                    elif stdscr is not None:  # Redundant but type checking purposes
                        stdscr.addch(y, x, entity.symbol, Colors.getAttr(entity.color))
                else:
                    if return_as_str:
                        if return_str is None:
                            return_str = ""
                        return_str += " "
                    elif stdscr is not None:
                        stdscr.addch(y, x, " ")
            if return_str is not None:
                return_str += "\n"

        return return_str

    def logEntityAtPos(self, y: int, x: int) -> None:
        dMin = -2
        dMax = 2
        Logger.info("Mmmmm")
        border_symbol: str = "@"

        context: str = f"{y+dMin:02} {border_symbol}"
        for dy in range(dMin, dMax + 1):
            for dx in range(dMin, dMax + 1):
                ent = self.getEntityAtPos(y + dy, x + dx)
                symbol = " " if ent is None else ent.symbol
                context += symbol

                if dx == dMax:
                    suf = (
                        f"{border_symbol}\n{y+dy+1:02} {border_symbol}"
                        if dy != dMax
                        else border_symbol
                    )
                    context += suf
        log: str = f"""
===++===++===++===++===
Entity At Pos (y:{y}, x:{x})
Ent: {self.getEntityAtPos(y,x)}
5x5 Context:
      |--- x:{x}
   {border_symbol * (1 + dMax + 1 + (-dMin) + 1)}
{context}
   {border_symbol * (1 + dMax + 1 + (-dMin) + 1)}
"""

        Logger.info(log)

    def getAliveEnemies(self) -> List[Entity]:
        return self.instances[EntityType.ENEMY]

    def getPlayerProjectiles(self) -> List[Entity]:
        return self.instances[EntityType.PLAYER_PROJECTILE]

    def getEnemyProjectiles(self) -> List[Entity]:
        return self.instances[EntityType.ENEMY_PROJECTILE]

    def deleteEntity(self, entity: Entity) -> None:
        instances = self.instances[entity.entity_type]
        instances.pop(instances.index(entity))

        ent_y, ent_x = entity.position
        self.setEntityAtPos(ent_y, ent_x, None)

    def getEntityAtPos(self, y: int, x: int, use_next_board=False) -> Optional[Entity]:
        """
        Assumes non-true board width/height
        """

        true_y = WindowConfig.convertToTrueY(y)
        true_x = WindowConfig.convertToTrueX(x)

        board = self.next_board if use_next_board else self.curr_board
        ents = board[true_y][true_x]
        if len(ents) > 1:
            raise Exception(
                "Do we want exception here? Should collision handlers have run at this point?"
            )
        return ents[0] if len(ents) == 1 else None

    def isPosOccupied(self, y: int, x: int) -> bool:
        return self.getEntityAtPos(y, x) != None

    def setEntityAtPos(
        self, y: int, x: int, entity: Optional[Entity], use_curr_board: bool = False
    ) -> None:
        """
        While we have a config for BOARD_WIDTH/HEIGHT, we also draw a border which
        makes us have a true width/height greater than the supplied values (unless border width = 0)

        As such this is a helper function to update the board but using the "game coordinates"
        ie ignoring the borders
        """

        true_y = WindowConfig.convertToTrueY(y)
        true_x = WindowConfig.convertToTrueX(x)

        try:
            assert (
                true_x >= WindowConfig.convertToTrueX(0)
                and true_x < WindowConfig.TRUE_BOARD_WIDTH - 1
            )
            assert (
                true_y >= WindowConfig.convertToTrueY(0)
                and true_y < WindowConfig.TRUE_BOARD_HEIGHT - 1
            )
        except:

            if entity is not None:
                Logger.info(
                    "Entity was moved out of bounds - Deleting (by not placing on next_board)."
                )
                self.deleteEntityReferences(entity)
                return
            else:
                raise Exception(
                    "Wha-. How are you setting an out-of-bounds pos to None?"
                )

        board = self.curr_board if use_curr_board else self.next_board
        if entity is not None:
            if entity in board[true_y][true_x]:
                raise Exception(f"Setting position of entity already set? - {entity}")
            board[true_y][true_x].append(entity)
            entity.setPosition(y, x)
        else:
            board[true_y][true_x] = []

        if use_curr_board:
            self.curr_board = board
        else:
            self.next_board = board

    def deleteEntityReferences(self, entity: Entity) -> None:
        self.instances[entity.entity_type].remove(entity)
