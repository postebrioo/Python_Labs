import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Union

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Document:
    doc_id: Union[str, int]
    path: Path
    text: str


def iter_documents(root: Path) -> Iterator[Document]:
    """Лінивий обхід папки з текстовими файлами або JSONL корпусу.
    
    Відкриває та читає по одному файлу за раз, звільняючи пам'ять після кожного кроку.
    """
    if not root.exists():
        raise FileNotFoundError(f"Каталог або файл не знайдено: {root}")

    # Підтримка JSONL файлів (для Лаби 6)
    if root.is_file() and root.suffix == ".jsonl":
        with open(root, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                yield Document(
                    doc_id=data.get("doc_id"),
                    path=Path(data.get("filename", "")),
                    text=data.get("text", "")
                )
        return

    # Підтримка як одного файлу, так і дерева директорій
    paths = [root] if root.is_file() else root.rglob("*.*")

    for path in paths:
        if path.suffix not in (".txt", ".md"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            yield Document(doc_id=path.stem, path=path, text=text)
        except Exception as err:
            logger.warning("Помилка читання файлу %s: %s", path, err)
            continue