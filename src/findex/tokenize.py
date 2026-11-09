import re
import unicodedata
from typing import Iterator

def tokenize(text: str) -> Iterator[str]:
    """
    Лінивий генератор токенів:
    - Нормалізує Unicode NFC на вхідному тексті.
    - Переводить у casefold.
    - Коректно виділяє слова з урахуванням діакритики та апострофів.
    """
    normalized = unicodedata.normalize('NFC', text).casefold()
    
    # Використовуємо значно надійніший шаблон із \w, який захоплює всі літери включно з діакритикою та апострофами
    pattern = r"[0-9a-zA-Zа-яА-ЯєЄіІїЇґҐ'’\w]+"
    
    for match in re.finditer(pattern, normalized):
        token = match.group().strip("'’")
        if not token or token.isdigit():
            continue
        yield token

tokenize_text = tokenize