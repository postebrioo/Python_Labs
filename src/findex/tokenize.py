import re
import unicodedata
from typing import Iterator

def tokenize(text: str) -> Iterator[str]:
    """
    Лінивий генератор токенів:
    - Застосовує Unicode NFC нормалізацію та casefold().
    - Зберігає внутрішні апострофи ('').
    - Розбиває дефісні слова на окремі токени.
    - Виключає суто числові токени.
    """
    # Нормалізація Unicode NFC та casefold
    normalized_text = unicodedata.normalize('NFC', text).casefold()
    
    # Регулярний вираз для пошуку слів (дозволяє внутрішні апострофи)
    # Знаходить послідовності букв та цифр, які можуть містити апостроф всередині
    pattern = r"[^\W\d_]+(?:'[^\W\d_]+)*"
    
    for match in re.finditer(pattern, normalized_text):
        token = match.group()
        # Виключаємо суто числові токени
        if token.isdigit():
            continue
        yield token

# Дублюємо ім'я для повної сумісності з іншими модулями (index.py)
tokenize_text = tokenize