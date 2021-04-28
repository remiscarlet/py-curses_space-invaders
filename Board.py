#!/usr/bin/env python3
from __future__ import annotations

import copy
import random

from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    # We only need to import Board for type checking purposes as we only use it
    # for type hinting in func signatures
    from SpaceInvaders import SpaceInvaders

from Config import Config
from Entity import Entity
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

    board: List[List[Optional[Entity]]]

    # If one imagines the enemies as a line that snakes at the top
    # of the screen, enemies_alive is ordered FILO
    enemies_alive: List[Entity] = []

    player_projectiles: List[Entity] = []
    enemy_projectiles: List[Entity] = []

    def __init__(
        self,
        player: Entity,
        enemies: List[Entity],
        num_enemies: int,
        space_invaders: "SpaceInvaders",
    ) -> None:
        self.__initializeBoard()
        self.__populateBoard(player, enemies, num_enemies)
        self.space_invaders = space_invaders

    def incrementScore(self) -> None:
        self.space_invaders.incrementScore()

    def __initializeBoard(self) -> None:
        """
        Initialize the board with empty cells and draw border
        """
        board: List[List[Optional[Entity]]] = [
            [None] * WindowConfig.TRUE_BOARD_WIDTH
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
                board[y][0] = Borders.INTERSECT_LEFT
                board[y][right_border_x] = Borders.INTERSECT_RIGHT
            else:
                # Draw a vertical line
                board[y][0] = Borders.VERTICAL
                board[y][right_border_x] = Borders.VERTICAL

        # Non-corner Horizontal borders
        for x in range(1, WindowConfig.TRUE_BOARD_WIDTH - 1):
            for y in rows_to_draw:
                board[y][x] = Borders.HORIZONTAL

        # Corners
        max_x = WindowConfig.TRUE_BOARD_WIDTH - 1
        max_y = WindowConfig.TRUE_BOARD_HEIGHT - 1
        board[0][0] = Borders.TOP_LEFT
        board[0][max_x] = Borders.TOP_RIGHT
        board[max_y][0] = Borders.BOT_LEFT
        board[max_y][max_x] = Borders.BOT_RIGHT

        self.board = board

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
        self.setEntityAtPos(player_y, player_x, player)
        player.setInitialPosition(player_y, player_x)

        enemy_y, enemy_x = 0, 0
        for i in range(num_enemies):
            enemy = copy.deepcopy(
                random.choice(enemies)
            )  # Deep copy to ensure no shared refs

            self.setEntityAtPos(enemy_y, enemy_x, enemy)
            enemy.setInitialPosition(enemy_y, enemy_x)

            dy, dx = enemy.genNextPosOffset(enemy_y, enemy_x, Config.ENEMY_SPACING)
            enemy_y += dy
            enemy_x += dx

            self.enemies_alive.append(enemy)

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

        projectile = copy.deepcopy(Entities.PLAYER_PROJECTILE)

        self.setEntityAtPos(proj_y, proj_x, projectile)
        projectile.setInitialPosition(proj_y, proj_x)

        if is_player_projectile:
            self.player_projectiles.append(projectile)
        else:
            self.enemy_projectiles.append(projectile)

    def getBoard(self) -> List[List[Optional[Entity]]]:
        return self.board

    def getAliveEnemies(self) -> List[Entity]:
        return self.enemies_alive

    def getPlayerProjectiles(self) -> List[Entity]:
        return self.player_projectiles

    def getEnemyProjectiles(self) -> List[Entity]:
        return self.enemy_projectiles

    def getEntityAtPos(self, y: int, x: int) -> Optional[Entity]:
        """
        Assumes non-true board width/height
        """

        true_y = WindowConfig.convertToTrueY(y)
        true_x = WindowConfig.convertToTrueX(x)

        return self.board[true_y][true_x]

    def isPosOccupied(self, y: int, x: int) -> bool:
        return self.getEntityAtPos(y, x) != None

    def setEntityAtPos(self, y: int, x: int, entity: Optional[Entity]) -> None:
        """
        While we have a config for BOARD_WIDTH/HEIGHT, we also draw a border which
        makes us have a true width/height greater than the supplied values (unless border width = 0)

        As such this is a helper function to update self.board but using the "game coordinates"
        ie ignoring the borders
        """

        true_y = WindowConfig.convertToTrueY(y)
        true_x = WindowConfig.convertToTrueX(x)

        Logger.debug(f"Setting true pos: {true_y},{true_x}")
        assert true_x > 0 and true_x < WindowConfig.TRUE_BOARD_WIDTH - 1
        assert true_y > 0 and true_y < WindowConfig.TRUE_BOARD_HEIGHT - 1

        self.board[true_y][true_x] = entity
