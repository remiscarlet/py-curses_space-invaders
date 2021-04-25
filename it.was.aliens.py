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

###########
# Configs #
###########


class Config:
    BOARD_HEIGHT: int = 15
    BOARD_WIDTH: int = 25
    ENEMY_COUNT: int = BOARD_WIDTH * 2
    ENEMY_SPACING: int = 2
    TICKS_PER_SECOND: int = 10

    TICKS_PER_ENEMY_MOVEMENT = 3

    LOG_PATH = "it.was.aliens.log"


#########################
# No touchy beyond here #
#########################


# Logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("[%(asctime)s][%(levelname)s] %(message)s")

file_handler = logging.FileHandler(Config.LOG_PATH)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


# Enums


class EntityType(enum.Enum):
    PLAYER = 0
    PLAYER_PROJECTILE = 1
    ENEMY = 2
    ENEMY_PROJECTILE = 3
    OBSTACLE = 4
    BORDER = 5


class InputType(enum.Enum):
    MOVEMENT = 0
    FIRE = 1
    QUIT = 2
    PAUSE = 3


# Classes


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
    def getAttr(color_id: int) -> None:
        if color_id not in Colors.mapping:
            raise Exception(f"Got a color ID that we haven't mapped! Got: {color_id}")
        return Colors.mapping[color_id]


class WindowConfig:
    """
    This class houses consts related to "window" sizes - ie cell width/lengths
    for various components of the UI.

    Layout:
    -------------  <-|-- BORDER_WIDTH
    | TITLE BAR |     |
    |-----------|   <-|-- TITLE_BAR_HEIGHT
    |           |      |
    |   GAME    |      |
    |  WINDOW   |      |
    |           |    <-|-- BOARD_HEIGHT # BOARD_HEIGHT does _not_ include the bottom border size due to it being the game board on the inside of borders.
    |-----------|     <-|-- BORDER_WIDTH
    | STATS BAR |        |
    -------------      <-|-- PLAYER_STATS_HEIGHT
    """

    BORDER_WIDTH: int = (
        1  # Eh... please don't change this for now. Multi-cell width borders are blegh.
    )

    TITLE_BAR_HEIGHT: int = 1 + BORDER_WIDTH  # 1 row for title + border width
    PLAYER_STATS_HEIGHT: int = 1 + BORDER_WIDTH  # 1 row for all stats + border width

    OFFSET_ROWS_TO_DRAW_HORIZONTAL: List[int] = [
        0,
        TITLE_BAR_HEIGHT,
        Config.BOARD_HEIGHT + BORDER_WIDTH,
        PLAYER_STATS_HEIGHT,
    ]

    TRUE_BOARD_WIDTH: int = Config.BOARD_WIDTH + 2 * BORDER_WIDTH
    TRUE_BOARD_HEIGHT: int = (
        sum(OFFSET_ROWS_TO_DRAW_HORIZONTAL) + 1
    )  # +1 because offset vs array length

    WINDOW_TITLE: str = "Space Invaders!"
    WINDOW_TITLE_DRAW_POS: Tuple[int, int] = (
        BORDER_WIDTH,
        TRUE_BOARD_WIDTH // 2 - len(WINDOW_TITLE) // 2,
    )  # (y, x)

    PAUSED_TEXT: str = "PAUSED"
    PAUSED_TEXT_DRAW_POS: Tuple[int, int] = (
        BORDER_WIDTH + TITLE_BAR_HEIGHT + (Config.BOARD_HEIGHT // 2),
        TRUE_BOARD_WIDTH // 2 - len(PAUSED_TEXT) // 2,
    )

    @staticmethod
    def getRowsToDrawHorizontals() -> List[int]:
        rows = list(itertools.accumulate(WindowConfig.OFFSET_ROWS_TO_DRAW_HORIZONTAL))
        assert rows[-1] == WindowConfig.TRUE_BOARD_HEIGHT - 1
        return rows

    @staticmethod
    def convertToTrueY(y: int) -> int:
        return WindowConfig.TITLE_BAR_HEIGHT + WindowConfig.BORDER_WIDTH + y

    @staticmethod
    def convertToTrueX(x: int) -> int:
        return WindowConfig.BORDER_WIDTH + x


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
        logger.debug(f"{self}: {msg}")

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

    def moveToNextPos(self, board: Board) -> None:
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

    def moveLeft(self, board: Board):
        self.__move(board, 0, -1)

    def canMoveRight(self, custom_pos: Optional[Tuple[int, int]] = None) -> bool:
        return self.__canMove(0, +1, custom_pos)

    def moveRight(self, board: Board):
        self.__move(board, 0, +1)

    def canMoveUp(self, custom_pos: Optional[Tuple[int, int]] = None) -> bool:
        return self.__canMove(-1, 0, custom_pos)

    def moveUp(self, board: Board):
        self.__move(board, -1, 0)  # Curses uses quadrant IV instead of the usual I

    def canMoveDown(self, custom_pos: Optional[Tuple[int, int]] = None) -> bool:
        return self.__canMove(+1, 0, custom_pos)

    def moveDown(self, board: Board):
        self.__move(board, +1, 0)

    def __canMove(self, dy: int, dx: int, custom_pos: Optional[Tuple[int, int]] = None):
        if custom_pos:
            old_y, old_x = custom_pos
        else:
            old_y, old_x = self.position
        new_y, new_x = (old_y + dy, old_x + dx)
        return not self.__isOutOfBounds(new_y, new_x)

    def __move(self, board: Board, dy: int, dx: int):
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


class Borders:
    VERTICAL = Entity("║", Colors.WHITE, EntityType.BORDER)
    HORIZONTAL = Entity("═", Colors.WHITE, EntityType.BORDER)
    TOP_LEFT = Entity("╔", Colors.WHITE, EntityType.BORDER)
    TOP_RIGHT = Entity("╗", Colors.WHITE, EntityType.BORDER)
    BOT_LEFT = Entity("╚", Colors.WHITE, EntityType.BORDER)
    BOT_RIGHT = Entity("╝", Colors.WHITE, EntityType.BORDER)
    INTERSECT_LEFT = Entity("╠", Colors.WHITE, EntityType.BORDER)
    INTERSECT_RIGHT = Entity("╣", Colors.WHITE, EntityType.BORDER)


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

    def __init__(self, player: Entity, enemies: List[Entity], num_enemies: int) -> None:
        self.__initializeBoard()
        self.__populateBoard(player, enemies, num_enemies)

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

        logger.info("===== Done populating initial entity positions.")

    def getBoard(self) -> List[List[Optional[Entity]]]:
        return self.board

    def getAliveEnemies(self) -> List[Entity]:
        return self.enemies_alive

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

        logger.debug(f"Setting true pos: {true_y},{true_x}")
        assert true_x > 0 and true_x < WindowConfig.TRUE_BOARD_WIDTH - 1
        assert true_y > 0 and true_y < WindowConfig.TRUE_BOARD_HEIGHT - 1

        self.board[true_y][true_x] = entity


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

        target_tick_dur_ns = 1 * 1000 * 1000 * 1000 / Config.TICKS_PER_SECOND
        curr_tick_start_ns = time.time_ns()
        logger.warning(
            f"target_dur: {target_tick_dur_ns} - curr_tick_start_ns: {curr_tick_start_ns}"
        )

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
            logger.info("Moving ship to the left")
            self.player.moveLeft(self.board)
        elif pressed_key in (curses.KEY_RIGHT, ord("d")) and self.player.canMoveRight():
            logger.info("Moving ship to the right")
            self.player.moveRight(self.board)

    def updateEnemies(self) -> None:
        for enemy in reversed(self.board.getAliveEnemies()):
            enemy.moveToNextPos(self.board)

    def togglePause(self) -> None:
        self.is_paused = not self.is_paused

    def update(self) -> None:
        logger.info("Input:")
        for group in InputType:
            pressed_key = self.inputManager.getLastPressedKeyForGroup(group)
            logger.info(f"{InputType(group).name}: {pressed_key}")

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
