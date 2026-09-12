import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Document:
    doc_id: str
    path: Path
    text: str


def iter_documents(root: Path) -> Iterator[Document]:
    """Лінивий обхід папки з текстовими файлами.
    
    Відкриває та читає по одному файлу за раз, звільняючи пам'ять після кожного кроку.
    """
    if not root.exists():
        raise FileNotFoundError(f"Каталог або файл не знайдено: {root}")

    # Підтримка як одного файлу, так і дерева директорій
    paths = [root] if root.is_file() else root.rglob("*.txt")

    for path in paths:
        try:
            # Читаємо конкретний файл з обов'язковим UTF-8
            text = path.read_text(encoding="utf-8", errors="replace")
            yield Document(doc_id=path.stem, path=path, text=text)
        except Exception as err:
            logger.warning("Помилка читання файлу %s: %s", path, err)
            continue