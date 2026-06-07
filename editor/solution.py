import sys
from typing import List


class CharacterStyle:
    """The Flyweight: Stores shared, immutable formatting state."""

    def __init__(self, font: str, size: int, color: str, bold: bool, italic: bool):
        self._font = font
        self._size = size
        self._color = color
        self._bold = bold
        self._italic = italic

    # Read-only properties
    @property
    def font(self) -> str:
        return self._font

    @property
    def size(self) -> int:
        return self._size

    @property
    def color(self) -> str:
        return self._color

    @property
    def bold(self) -> bool:
        return self._bold

    @property
    def italic(self) -> bool:
        return self._italic


class StyleFactory:
    """The Flyweight Factory: Ensures unique styles are cached and reused."""

    _styles = {}

    @classmethod
    def get_style(
        cls, font: str, size: int, color: str, bold: bool, italic: bool
    ) -> CharacterStyle:
        key = (font, size, color, bold, italic)
        if key not in cls._styles:
            cls._styles[key] = CharacterStyle(font, size, color, bold, italic)
        return cls._styles[key]

    @classmethod
    def total_styles_created(cls) -> int:
        return len(cls._styles)


class FormattedCharacter:
    """Contextual object containing extrinsic data (the literal character)
    and a reference to the intrinsic Flyweight style."""

    def __init__(self, char: str, style: CharacterStyle):
        self.char = char
        self.style = style  # Shared reference


class Row:
    """Represents a single line/row of text or grid elements."""

    def __init__(self):
        self.characters: List[FormattedCharacter] = []

    def insert_at(self, col: int, formatted_char: FormattedCharacter):
        if col >= len(self.characters):
            self.characters.append(formatted_char)
        else:
            self.characters.insert(col, formatted_char)

    def delete_at(self, col: int) -> FormattedCharacter:
        if 0 <= col < len(self.characters):
            return self.characters.pop(col)
        raise IndexError("Column index out of bounds.")


class Document:
    """The core Receiver object representing the grid matrix."""

    def __init__(self):
        self.rows: List[Row] = [Row()]  # Start with one empty row

    def insert_char(self, row: int, col: int, char: str, style: CharacterStyle):
        while row >= len(self.rows):
            self.rows.append(Row())

        formatted_char = FormattedCharacter(char, style)
        self.rows[row].insert_at(col, formatted_char)

    def delete_char(self, row: int, col: int) -> FormattedCharacter:
        if row < len(self.rows):
            return self.rows[row].delete_at(col)
        raise IndexError("Row index out of bounds.")

    def render(self):
        """Helper to debug print the grid."""
        for i, r in enumerate(self.rows):
            chars = "".join([fc.char for fc in r.characters])
            print(f"Row {i}: {chars}")


from abc import ABC, abstractmethod


class Command(ABC):
    """Abstract Command interface."""

    @abstractmethod
    def execute(self) -> bool:
        pass

    @abstractmethod
    def undo(self):
        pass


class InsertCharacterCommand(Command):
    """Concrete Command for adding characters to the text matrix."""

    def __init__(
        self, doc: Document, row: int, col: int, char: str, style: CharacterStyle
    ):
        self.doc = doc
        self.row = row
        self.col = col
        self.char = char
        self.style = style

    def execute(self) -> bool:
        self.doc.insert_char(self.row, self.col, self.char, self.style)
        return True

    def undo(self):
        # To reverse an insertion, we delete the item at that position
        self.doc.delete_char(self.row, self.col)


class DeleteCharacterCommand(Command):
    """Concrete Command for removing characters."""

    def __init__(self, doc: Document, row: int, col: int):
        self.doc = doc
        self.row = row
        self.col = col
        self.deleted_char: FormattedCharacter = None

    def execute(self) -> bool:
        try:
            self.deleted_char = self.doc.delete_char(self.row, self.col)
            return True
        except IndexError:
            return False

    def undo(self):
        # To reverse a deletion, we re-insert the cached character along with its style
        if self.deleted_char:
            self.doc.insert_char(
                self.row, self.col, self.deleted_char.char, self.deleted_char.style
            )


class TextEditor:
    """The Invoker: Exposes user operations and handles history stacks."""

    def __init__(self):
        self.document = Document()
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []

    def execute_command(self, command: Command):
        if command.execute():
            self.undo_stack.append(command)
            self.redo_stack.clear()  # New operations break the redo chain

    def undo(self):
        if not self.undo_stack:
            print("--- Nothing to Undo ---")
            return
        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)

    def redo(self):
        if not self.redo_stack:
            print("--- Nothing to Redo ---")
            return
        command = self.redo_stack.pop()
        command.execute()
        self.undo_stack.append(command)
