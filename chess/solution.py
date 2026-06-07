from abc import ABC, abstractmethod


class MoveStrategy(ABC):
    """Abstract Strategy defining a type of movement vector."""

    @abstractmethod
    def is_valid_move(
        self, start_row: int, start_col: int, end_row: int, end_col: int
    ) -> bool:
        pass


class StraightMoveStrategy(MoveStrategy):
    """Allows horizontal or vertical sliding (Rook mechanics)."""

    def is_valid_move(
        self, start_row: int, start_col: int, end_row: int, end_col: int
    ) -> bool:
        return start_row == end_row or start_col == end_col


class DiagonalMoveStrategy(MoveStrategy):
    """Allows precise diagonal sliding (Bishop mechanics)."""

    def is_valid_move(
        self, start_row: int, start_col: int, end_row: int, end_col: int
    ) -> bool:
        return abs(start_row - end_row) == abs(start_col - end_col)


class KnightMoveStrategy(MoveStrategy):
    """Allows L-shaped jumps: 2 steps one way, 1 step perpendicular."""

    def is_valid_move(
        self, start_row: int, start_col: int, end_row: int, end_col: int
    ) -> bool:
        row_diff = abs(start_row - end_row)
        col_diff = abs(start_col - end_col)
        return (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)


from enum import Enum
from typing import List


class Color(Enum):
    WHITE = 1
    BLACK = 2


class PieceType(Enum):
    ROOK = 1
    BISHOP = 2
    QUEEN = 3
    KNIGHT = 4


class Piece:
    """The core Domain Object composed of one or more movement strategies."""

    def __init__(
        self, piece_type: PieceType, color: Color, strategies: List[MoveStrategy]
    ):
        self.type = piece_type
        self.color = color
        self.strategies = strategies

    def can_move(
        self, start_row: int, start_col: int, end_row: int, end_col: int
    ) -> bool:
        # A piece can move if ANY of its assigned strategies return True
        return any(
            strat.is_valid_move(start_row, start_col, end_row, end_col)
            for strat in self.strategies
        )


class PieceFactory:
    """The Factory: Instantiates concrete pieces with their mathematical strategies."""

    @staticmethod
    def create_piece(piece_type: PieceType, color: Color) -> Piece:
        if piece_type == PieceType.ROOK:
            return Piece(piece_type, color, [StraightMoveStrategy()])

        elif piece_type == PieceType.BISHOP:
            return Piece(piece_type, color, [DiagonalMoveStrategy()])

        elif piece_type == PieceType.QUEEN:
            # The Queen elegantly reuses BOTH straight and diagonal strategies!
            return Piece(
                piece_type, color, [StraightMoveStrategy(), DiagonalMoveStrategy()]
            )

        elif piece_type == PieceType.KNIGHT:
            return Piece(piece_type, color, [KnightMoveStrategy()])

        raise ValueError(f"Unknown piece type: {piece_type}")


from typing import Optional


class Board:
    """Manages the 8x8 spatial matrix and validates structural board rules."""

    def __init__(self):
        self.grid: List[List[Optional[Piece]]] = [
            [None for _ in range(8)] for _ in range(8)
        ]

    def place_piece(self, row: int, col: int, piece: Piece) -> None:
        self.grid[row][col] = piece

    def get_piece(self, row: int, col: int) -> Optional[Piece]:
        return self.grid[row][col]

    def validate_and_move(
        self, start_row: int, start_col: int, end_row: int, end_col: int
    ) -> bool:
        # 1. Boundary Check
        if not (
            0 <= start_row < 8
            and 0 <= start_col < 8
            and 0 <= end_row < 8
            and 0 <= end_col < 8
        ):
            return False

        piece = self.grid[start_row][start_col]
        if not piece:
            return False  # Can't move a piece that doesn't exist

        # 2. Destination Friendly-Fire Check
        target_piece = self.grid[end_row][end_col]
        if target_piece and target_piece.color == piece.color:
            return False  # Can't capture your own color

        # 3. Structural Strategy Check
        if not piece.can_move(start_row, start_col, end_row, end_col):
            return False

        # 4. Collision/Obstruction Check (Crucial for sliding pieces like Rooks/Queens)
        if piece.type != PieceType.KNIGHT:
            if not self._is_path_clear(start_row, start_col, end_row, end_col):
                return False

        # Execute Move
        self.grid[end_row][end_col] = piece
        self.grid[start_row][start_col] = None
        return True

    def _is_path_clear(
        self, start_row: int, start_col: int, end_row: int, end_col: int
    ) -> bool:
        """Traces the line of sight to ensure sliding pieces don't phase through objects."""
        row_step = max(-1, min(1, end_row - start_row))  # Normalizes to -1, 0, or 1
        col_step = max(-1, min(1, end_col - start_col))

        curr_row = start_row + row_step
        curr_col = start_col + col_step

        while curr_row != end_row or curr_col != end_col:
            if self.grid[curr_row][curr_col] is not None:
                return False  # Obstruction hit!
            curr_row += row_step
            curr_col += col_step

        return True
