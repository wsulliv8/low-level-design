"""
class Game:
    - board: Board
    - player1: Player
    - player2: Player
    - currentPlayer: Player
    - state: GameState        // IN_PROGRESS, WON, DRAW
    - winner: Player?

    + Game(player1, player2)
    + makeMove(player, column) -> bool
    + getCurrentPlayer() -> Player
    + getGameState() -> GameState
    + getWinner() -> Player?
    + getBoard() -> Board

class Board:
    - rows: int = 6
    - cols: int = 7
    - grid: DiscColor?[rows][cols]

    + Board()
    + getRows() -> int
    + getCols() -> int
    + canPlace(column) -> bool
    + placeDisc(column, color) -> int
    + isFull() -> bool
    + checkWin(row, column, color) -> bool
    + getCell(row, column) -> DiscColor?

class Player:
    - name: string
    - color: DiscColor

    + Player(name, color)
    + getName() -> string
    + getColor() -> DiscColor

enum GameState:
    IN_PROGRESS
    WON
    DRAW

enum DiscColor:
    RED
    YELLOW
"""

from enum import Enum
from typing import Optional


class GameState(Enum):
    IN_PROGRESS = "IN_PROGRESS"
    WON = "WON"
    DRAW = "DRAW"


class DiscColor(Enum):
    RED = "RED"
    YELLOW = "YELLOW"


class Player:
    def __init__(self, name: str, color):
        self.name = name
        self.color = color  # DiscColor


class Board:
    def __init__(self, rows: int = 6, cols: int = 7):
        self.rows = rows
        self.cols = cols
        self.grid: list[list[Optional[DiscColor]]] = [
            [None for _ in range(cols)] for _ in range(rows)
        ]

    def get_rows(self) -> int:
        return self.rows

    def get_cols(self) -> int:
        return self.cols

    def can_place(self, column: int) -> bool:
        if column < 0 or column >= self.cols:
            return False
        return self.grid[0][column] is None

    def place_disc(self, column: int, color: DiscColor) -> int:
        if not self.can_place(column):
            return -1

        for row in range(self.rows - 1, -1, -1):
            if self.grid[row][column] is None:
                self.grid[row][column] = color
                return row

        return -1

    def check_win(self, row: int, column: int, color: DiscColor) -> bool:
        if not self._in_bounds(row, column) or self.grid[row][column] != color:
            return False

        directions = [(0, 1), (1, 0), (1, 1), (-1, 1)]

        for dr, dc in directions:
            count = 1
            count += self._count_in_direction(row, column, dr, dc, color)
            count += self._count_in_direction(row, column, -dr, -dc, color)
            if count >= 4:
                return True
        return False

    def is_full(self) -> bool:
        return all(self.grid[0][c] is not None for c in range(self.cols))

    def get_cell(self, row: int, column: int) -> Optional[DiscColor]:
        if not self._in_bounds(row, column):
            return None
        return self.grid[row][column]

    def _count_in_direction(
        self, row: int, column: int, dr: int, dc: int, color: DiscColor
    ) -> int:
        count = 0
        r = row + dr
        c = column + dc
        while self._in_bounds(r, c) and self.grid[r][c] == color:
            count += 1
            r += dr
            c += dc
        return count

    def _in_bounds(self, row: int, column: int) -> bool:
        return 0 <= row < self.rows and 0 <= column < self.cols


class Game:
    def __init__(self, player1, player2):
        self.board = Board()
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.state = GameState.IN_PROGRESS
        self.winner: Optional["Player"] = None

    def make_move(self, player, column: int) -> bool:
        if self.state is not GameState.IN_PROGRESS:
            return False
        if player is not self.current_player:
            return False

        row = self.board.place_disc(column, player.color)
        if row == -1:
            return False

        if self.board.check_win(row, column, player.color):
            self.state = GameState.WON
            self.winner = player
        elif self.board.is_full():
            self.state = GameState.DRAW
        else:
            self.current_player = (
                self.player2 if self.current_player is self.player1 else self.player1
            )

        return True

    def get_current_player(self) -> Player:
        return self.current_player

    def get_game_state(self) -> GameState:
        return self.state

    def get_winner(self) -> Optional[Player]:
        return self.winner

    def get_board(self) -> Board:
        return self.board
