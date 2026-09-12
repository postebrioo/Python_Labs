import sys
from pathlib import Path

# Автоматично додаємо папку src до шляхів пошуку модулів
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from findex.tokenize import tokenize


def test_tokenize_coverage() -> None:
    # 1. Регістр та змішаний текст
    assert list(tokenize("Hello World")) == ["hello", "world"]

    # 2. Кирилиця
    assert list(tokenize("Швидкий потік слів")) == ["швидкий", "потік", "слів"]

    # 3. Апострофи (український та англійський)
    assert list(tokenize("п'ять м’ячів don't")) == ["п'ять", "м’ячів", "don't"]

    # 4. NFC нормалізація (комбінований наголос e + \u0301)
    combined = "cafe\u0301"
    precomposed = "café"
    assert list(tokenize(combined)) == list(tokenize(precomposed)) == ["café"]

    # 5. Німецький casefold (есцет)
    assert list(tokenize("Fluß")) == ["fluss"]

    # 6. Пунктуація та розділювачі
    assert list(tokenize("один, два; три!")) == ["один", "два", "три"]

    # 7. Дефіси розбиваються на окремі слова
    assert list(tokenize("state-of-the-art")) == ["state", "of", "the", "art"]

    # 8. Цифри та ізольовані знаки ігноруються
    assert list(tokenize("версія 2 та 100 пунктів")) == ["версія", "та", "пунктів"]

    # 9. Порожній рядок та пробіли
    assert list(tokenize("")) == []
    assert list(tokenize("   \n\t  ")) == []


if __name__ == "__main__":
    test_tokenize_coverage()
    print("Усі тести пройдено успішно!")