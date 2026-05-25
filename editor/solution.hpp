#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
#include <mutex>
#include <unordered_map>
#include <vector>

enum class TextStyle { Regular, Bold, Italic };

struct StyleKey {
  TextStyle style{TextStyle::Regular};
  size_t size{10};
  uint32_t color{0xFFFFFFFF};

  bool operator==(const StyleKey &other) const {
    return style == other.style && size == other.size && color == other.color;
  }
};

struct StyleKeyHash {
  size_t operator()(const StyleKey &sk) const {
    auto [style, size, color] = sk;
    size_t h1 = std::hash<int>{}(static_cast<int>(style));
    size_t h2 = std::hash<size_t>{}(size);
    size_t h3 = std::hash<uint32_t>{}(color);
    return h1 ^ (h2 << 1) ^ (h3 << 2);
  }
};

class StyleFactory {
private:
  std::unordered_map<StyleKey, std::shared_ptr<const StyleKey>, StyleKeyHash>
      stylePool;
  std::mutex factoryMtx;

public:
  std::shared_ptr<const StyleKey> getStyle(TextStyle ts, size_t s, uint32_t c);
};

struct Cursor {
  size_t row{0};
  size_t col{0};
};

class Command {
public:
  virtual ~Command();
  virtual void execute() = 0;
  virtual void undo() = 0;
};

class Document;

class InsertCommand : public Command {
private:
  Document &document;
  char ch;
  size_t row, col;
  std::shared_ptr<const StyleKey> style;

public:
  InsertCommand(Document &d, char c, size_t r, size_t cl,
                std::shared_ptr<const StyleKey> s)
      : document(d), ch(c), row(r), col(cl), style(s) {};

  void execute() override;
  void undo() override;
};

class DeleteCommand : public Command {
private:
  Document &document;
  char deletedChar{'\0'};
  size_t row, col;

public:
  DeleteCommand(Document &d, size_t r, size_t cl)
      : document(d), row(r), col(cl) {};

  void execute() override;
  void undo() override;
};

class UpdateStyleCommand : public Command {
private:
  Document &document;
  size_t row1, col1, row2, col2;
  std::shared_ptr<const StyleKey> style;

public:
  UpdateStyleCommand(Document &d, size_t r1, size_t c1, size_t r2, size_t c2,
                     std::shared_ptr<const StyleKey> s)
      : document(d), row1(r1), col1(c1), row2(r2), col2(c2), style(s) {};

  void execute() override;
  void undo() override;
};

class Document {
private:
  std::vector<std::string> lines;
  std::vector<std::vector<std::shared_ptr<const StyleKey>>> styles;
  Cursor cursor;
  mutable std::mutex docMtx;

  size_t rows, cols;

public:
  Document(size_t r, size_t c) : rows(r), cols(c) {
    lines.emplace_back("");
    styles.emplace_back(std::vector<std::shared_ptr<const StyleKey>>());
  };

  void setCursor(size_t r, size_t c);
  Cursor getCursor() const { return cursor; }

  void insertAt(size_t r, size_t c, char ch, std::shared_ptr<const StyleKey>);
  char deleteAt(size_t r, size_t c);
  void applyStyleToRange(size_t r1, size_t c1, size_t r2, size_t c2,
                         const StyleKey &sk);
};

class TextEditor {
private:
  Document document;
  StyleFactory factory;
  std::vector<std::unique_ptr<Command>> undoStack;
  std::vector<std::unique_ptr<Command>> redoStack;
  std::mutex editorMtx;

public:
  TextEditor(size_t r, size_t c) : document(r, c) {}

  void run();
  void handleTypeKey(char ch, TextStyle ts, size_t s, uint32_t c);
  void handleBackspace();
  void handleUndo();
  void handleRedo();
};
