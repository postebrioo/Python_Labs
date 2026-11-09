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
    # Спочатку приводимо до NFC та casefold, щоб комбіновані символи об'єдналися в єдину літеру (наприклад, é)
    normalized_text = unicodedata.normalize('NFC', text).casefold()
    
    # Регулярний вираз для пошуку слів з урахуванням апострофів
    pattern = r"[0-9a-zA-Zа-яА-ЯєЄіІїЇґҐ'’]+"
    
    for match in re.finditer(pattern, normalized_text):
        token = match.group().strip("'’")
        if not token or token.isdigit():
            continue
        yield token

tokenize_text = tokenize