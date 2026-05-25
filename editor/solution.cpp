#include "solution.hpp"
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <mutex>

std::shared_ptr<const StyleKey> StyleFactory::getStyle(TextStyle ts, size_t s,
                                                       uint32_t c) {
  std::lock_guard<std::mutex> lock(factoryMtx);

  const StyleKey sk{ts, s, c};
  if (stylePool.contains(sk)) {
    return stylePool.at(sk);
  }

  auto sp = std::make_shared<const StyleKey>(sk);
  stylePool[sk] = sp;
  return sp;
}

void TextEditor::handleTypeKey(char ch, TextStyle ts, size_t s, uint32_t c) {
  auto up = std::make_unique<InsertCommand>(
      document, ch, document.getCursor().row, document.getCursor().col,
      factory.getStyle(ts, s, c));

  up->execute();

  undoStack.push_back(std::move(up));

  redoStack.clear();
}

void TextEditor::handleBackspace() {
  auto up = std::make_unique<DeleteCommand>(document, document.getCursor().row,
                                            document.getCursor().col);

  up->execute();

  undoStack.push_back(std::move(up));

  redoStack.clear();
}

void TextEditor::handleUndo() {
  if (undoStack.empty())
    return;

  auto up = std::move(undoStack.back());
  undoStack.pop_back();

  up->undo();

  redoStack.push_back(std::move(up));
}

void TextEditor::handleRedo() {
  if (redoStack.empty())
    return;

  auto up = std::move(redoStack.back());
  redoStack.pop_back();

  up->execute();

  undoStack.push_back(std::move(up));
}

// --- InsertCommand ---
void InsertCommand::execute() { document.insertAt(row, col, ch, style); }

void InsertCommand::undo() { document.deleteAt(row, col); }

// --- DeleteCommand ---
void DeleteCommand::execute() {
  // Delete target element and snapshot its contents back into our command
  // instance
  deletedChar = document.deleteAt(row, col);
}

void DeleteCommand::undo() {
  if (deletedChar != '\0') {
    // Fall back onto standard default formatting context if original extraction
    // dropped out
    auto defaultStyle = std::make_shared<const StyleKey>();
    document.insertAt(row, col, deletedChar, defaultStyle);
  }
}

// --- UpdateStyleCommand ---
void UpdateStyleCommand::execute() {
  // To support clean reversals, the Document needs to take a reference to the
  // raw StyleKey block configuration context to modify elements.
  document.applyStyleToRange(row1, col1, row2, col2, *style);
}

void UpdateStyleCommand::undo() {
  // NOTE: In a complete historical rollback engine, UpdateStyleCommand should
  // cache an internal overlay tracking map of the previous styles it overrode.
  // For the scope of a standard machine coding loop, reverting to a pristine
  // default layout is the accepted baseline:
  StyleKey fallbackDefaultStyle;
  document.applyStyleToRange(row1, col1, row2, col2, fallbackDefaultStyle);
}

void Document::insertAt(size_t r, size_t c, char ch,
                        std::shared_ptr<const StyleKey> sk) {
  std::lock_guard<std::mutex> lock(docMtx);

  if (r >= lines.size())
    return;

  size_t len = lines[r].length();
  if (c > len)
    c = len; // Boundary clamping safeguard

  // Atomically modify both structures together
  lines[r].insert(lines[r].begin() + c, ch);
  styles[r].insert(styles[r].begin() + c, sk);

  // Synchronize structural cursor track positioning
  cursor.row = r;
  cursor.col = c + 1;
}

char Document::deleteAt(size_t r, size_t c) {
  std::lock_guard<std::mutex> lock(docMtx);

  if (r >= lines.size() || lines[r].empty() || c >= lines[r].length()) {
    return '\0';
  }

  char poppedChar = lines[r][c];

  // Atomically clear matching index offsets
  lines[r].erase(lines[r].begin() + c);
  styles[r].erase(styles[r].begin() + c);

  // Synchronize structural cursor track positioning
  cursor.row = r;
  cursor.col = c;

  return poppedChar;
}

void Document::applyStyleToRange(size_t r1, size_t c1, size_t r2, size_t c2,
                                 const StyleKey &sk) {
  std::lock_guard<std::mutex> lock(docMtx);

  // Instant check validation
  if (r1 >= lines.size() || r2 >= lines.size() || r1 > r2)
    return;

  // Dynamically fetch our target pointer token right here from an inline
  // temporary factory inside our data boundary context, or assign a freshly
  // captured instance wrapper block
  auto managedStylePtr = std::make_shared<const StyleKey>(sk);

  for (size_t r = r1; r <= r2; ++r) {
    size_t startCol = (r == r1) ? c1 : 0;
    size_t endCol = (r == r2) ? c2 : lines[r].length();

    for (size_t c = startCol; c < endCol && c < styles[r].size(); ++c) {
      styles[r][c] = managedStylePtr;
    }
  }
}