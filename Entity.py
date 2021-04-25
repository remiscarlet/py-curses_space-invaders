#!/usr/bin/env python3
from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from Board import Board

from Config import Config
from WindowConfig import WindowConfig
from EntityType import EntityType
from Logger import Logger


class Entity:
    """
    With the exception of text drawn on the screen, all other
    elements that are drawn on the screen including borders, player, enemies, projectiles, etc
    are all "Entities".

    This class handles state and movement/updates for any and all entities.

    Border entities do not have an initial position set with the understanding that border entities
    should never be moved with a canMove*() or move*() method call.
    """

    symbol: str
    color: int
    entity_type: EntityType

    sizes: WindowConfig

    position: Tuple[int, int]  # y,x as per curses format

    ticks_since_last_move: int = 0

    def __init__(self, symbol: str, color: int, entity_type: EntityType) -> None:
        self.symbol = symbol
        self.color = color
        self.entity_type = entity_type

    def __str__(self) -> str:
        try:
            return f"{EntityType(self.entity_type).name}-{self.symbol}-{self.position}"
        except AttributeError:
            return f"{EntityType(self.entity_type).name}-{self.symbol}-NoPos"

    def __log(self, msg: str) -> None:
        Logger.debug(f"{self}: {msg}")

    def setInitialPosition(self, y: int, x: int) -> None:
        """
        This function assumes BOARD_WIDTH/HEIGHT as the bounds and _not_ TRUE_BOARD_WIDTH/HEIGHT
        """
        self.__log(f"Setting initial position: {y}, {x} - is true size")
        self.position = (y, x)

    def getPos(self) -> Tuple[int, int]:
        try:
            return self.position
        except:
            raise Exception(
                "This Entity doesn't have a position set but getPos() was called!"
            )

    def genNextPosOffset(
        self, curr_y: int, curr_x: int, depth: int = 1
    ) -> Tuple[int, int]:
        if self.entity_type == EntityType.PLAYER_PROJECTILE:
            return (-1, 0)
        elif self.entity_type == EntityType.ENEMY_PROJECTILE:
            return (+1, 0)
        elif self.entity_type in (EntityType.PLAYER, EntityType.ENEMY):
            return self.genNextPosOffsetForNonProjectile(curr_y, curr_x, depth)
        else:
            raise Exception(
                f"Tried to get the next position of an entity that does not move! Self: {self}"
            )

    def genNextPosOffsetForNonProjectile(
        self, curr_y: int, curr_x: int, depth: int = 1
    ) -> Tuple[int, int]:
        """
        Assumes the correct "next pos" is open and valid to move to.

        The `depth` arg is "how many steps ahead do you want", ie can get
        the pos for
        """

        self.__log(f"Generating next deltas from pos: {curr_y},{curr_x}")

        dx = -1 if curr_y % 2 == 1 else +1  # Left if odd row, Right if even row
        if dx == -1:
            can_move_horizontal = self.canMoveLeft((curr_y, curr_x))
        else:
            can_move_horizontal = self.canMoveRight((curr_y, curr_x))

        if not can_move_horizontal:
            if not self.canMoveDown():
                raise Exception(
                    "genNextPos() determined moving down is impossible! (Game over?)"
                )
            self.__log(f"Next delta: {+1},{0}")
            offset = (+1, 0)
        else:
            self.__log(f"Next delta: {0},{dx}")
            offset = (0, dx)

        if depth > 1:
            offset_y, offset_x = offset
            next_y, next_x = curr_y + offset_y, curr_x + offset_x
            next_offset_y, next_offset_x = self.genNextPosOffset(
                next_y, next_x, depth - 1
            )

            offset = (offset_y + next_offset_y, offset_x + next_offset_x)

        self.__log(f"offset for depth:{depth} - {offset}")
        return offset

    def moveToNextPos(self, board: "Board") -> None:
        """
        Assumes this method is called on Entity every tick.
        """
        if self.ticks_since_last_move > Config.TICKS_PER_ENEMY_MOVEMENT:
            old_y, old_x = self.position
            dy, dx = self.genNextPosOffset(old_y, old_x)
            new_y, new_x = old_y + dy, old_x + dx

            entity = board.getEntityAtPos(new_y, new_x)
            if entity != None:
                # TODO: Implement hit detection. Maybe here.
                raise Exception(
                    f"Tried moving entity but next pos was occupied! New pos: {new_y},{new_x}"
                )

            self.__move(board, dy, dx)
            self.ticks_since_last_move = 0

        self.ticks_since_last_move += 1

    def __isOutOfBounds(self, y: int, x: int) -> bool:
        """
        Assumes non-true boardsize. Ie, Config.BOARD_WIDTH/HEIGHT instead of TRUE_BOARD_WIDTH/HEIGHT
        """

        self.__log(
            f"x:{x} < 0 or x:{x} > {Config.BOARD_WIDTH - 1} or y:{y} < 0 or y:{y} > {Config.BOARD_HEIGHT - 1}"
        )

        return (
            x < 0 or x > Config.BOARD_WIDTH - 1 or y < 0 or y > Config.BOARD_HEIGHT - 1
        )

    """
    All move* methods will error out if the destination
    of the move is either already occupied or out of bounds.

    All canMove* functions do _not_ check if the next pos is occupied.
    """

    def canMoveLeft(self, custom_pos: Optional[Tuple[int, int]] = None) -> bool:
        return self.__canMove(0, -1, custom_pos)

    def moveLeft(self, board: "Board"):
        self.__move(board, 0, -1)

    def canMoveRight(self, custom_pos: Optional[Tuple[int, int]] = None) -> bool:
        return self.__canMove(0, +1, custom_pos)

    def moveRight(self, board: "Board"):
        self.__move(board, 0, +1)

    def canMoveUp(self, custom_pos: Optional[Tuple[int, int]] = None) -> bool:
        return self.__canMove(-1, 0, custom_pos)

    def moveUp(self, board: "Board"):
        self.__move(board, -1, 0)  # Curses uses quadrant IV instead of the usual I

    def canMoveDown(self, custom_pos: Optional[Tuple[int, int]] = None) -> bool:
        return self.__canMove(+1, 0, custom_pos)

    def moveDown(self, board: "Board"):
        self.__move(board, +1, 0)

    def __canMove(self, dy: int, dx: int, custom_pos: Optional[Tuple[int, int]] = None):
        if custom_pos:
            old_y, old_x = custom_pos
        else:
            old_y, old_x = self.position
        new_y, new_x = (old_y + dy, old_x + dx)
        return not self.__isOutOfBounds(new_y, new_x)

    def __move(self, board: "Board", dy: int, dx: int):
        old_y, old_x = self.position
        new_y, new_x = (old_y + dy, old_x + dx)

        if self.__isOutOfBounds(new_y, new_x):
            raise Exception("Entity is being moved out of bounds!")

        if board.isPosOccupied(new_y, new_x):
            self.__log(f"{board.getEntityAtPos(new_y, new_x)}")
            raise Exception("Destination cell is already occupied!")

        self.__log(f"Moved from old pos {old_y},{old_x} to new pos {new_y},{new_x}")

        board.setEntityAtPos(old_y, old_x, None)
        board.setEntityAtPos(new_y, new_x, self)

        self.position = (new_y, new_x)
