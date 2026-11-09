import re
import unicodedata
from typing import Iterator

def tokenize(text: str) -> Iterator[str]:
    """
    Лінивий генератор токенів:
    - Застосовує Unicode NFC нормалізацію та casefold() на самому початку.
    - Зберігає внутрішні апострофи (' та ’).
    - Виключає суто числові токени.
    """
    # Спочатку приводимо весь текст до NFC, щоб символи наголосу злилися з літерами
    normalized_text = unicodedata.normalize('NFC', text).casefold()
    
    # Паттерн для пошуку слів з урахуванням апострофів
    pattern = r"[0-9a-zA-Zа-яА-ЯєЄіІїЇґҐ'’]+"
    
    for match in re.finditer(pattern, normalized_text):
        token = match.group().strip("'’")
        if not token or token.isdigit():
            continue
        yield token

# Дублюємо для повної сумісності
tokenize_text = tokenize