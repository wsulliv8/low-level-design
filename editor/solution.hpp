/*

enum style
-bold, italic, regular

struct StyleKey
- style
- size
- color
- operator == ()

struct StyleKeyHash
- operator () ()

class StyleFactory
- set(styles)
- getStyle()

struct Character
- character
- shared style pointer

struct Cursor {
- row
- col
}

class TextEditor
- Document document
- StyleFactory factory
- vector<Command> undoStack
- vector<Command> redoStack
- executeCommand()
- undoCommand()
- redoCommand()

class Document
- vector<string> lines
- vector<vector<Style>> styles
- setCursor()
- insertAtCursor()
- deleteAtCursor()
- applyStyleToRange()


interface class Command
- execute()
- undo()

InsertCharCommand : Command

DeleteCharCommand : Command

UpdateStyleCommand : Command

*/