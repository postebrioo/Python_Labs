import re
import unicodedata
from typing import Iterator

# Словні токени: літери (будь-якої абетки), які можуть містити апостроф усередині
TOKEN_PATTERN = re.compile(r"\b[^\W\d_]+(?:['’][^\W\d_]+)*\b", re.UNICODE)


def tokenize(text: str) -> Iterator[str]:
    """Стрімінговий токенізатор.
    
    1. Приводить рядок до форми NFC.
    2. Виконує повний casefold.
    3. Ліниво повертає збіги за допомогою finditer.
    """
    normalized = unicodedata.normalize("NFC", text)
    folded = normalized.casefold()

    for match in TOKEN_PATTERN.finditer(folded):
        yield match.group(0)