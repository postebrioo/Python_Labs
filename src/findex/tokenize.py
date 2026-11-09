import re
import unicodedata
from typing import Iterator

def tokenize(text: str) -> Iterator[str]:
    """
    Лінивий генератор токенів:
    - Застосовує Unicode NFC нормалізацію та casefold().
    - Зберігає внутрішні апострофи (' та ’).
    - Виключає суто числові токени.
    """
    normalized_text = unicodedata.normalize('NFC', text).casefold()
    
    # Підтримуємо обидва види апострофів: звичайний ' та український ’
    pattern = r"[0-9a-zA-Zа-яА-ЯєЄіІїЇґҐ'’]+"
    
    for match in re.finditer(pattern, normalized_text):
        token = match.group().strip("'’")
        if not token or token.isdigit():
            continue
        yield token

# Дублюємо для сумісності
tokenize_text = tokenize