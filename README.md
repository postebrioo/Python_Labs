\# Lab 01 — Streams, Not Lists



\## Corpus

Text files downloaded from Project Gutenberg stored in `data/`.



\## Tokenizer Policy

\- Applied Unicode NFC normalization and `casefold()`.

\- Internal apostrophes are preserved (`'`).

\- Hyphenated words are split into separate tokens.

\- Purely numeric tokens are excluded.



\## Measurements (M4)



| Version | Documents | Peak memory | Elapsed |

|  eager  |    6      | 36.68 MB    | 2.299 s |

|  lazy   |    6      | 22.67 MB    | 3.239 s |



\### Why the numbers differ

The eager version loads all documents into memory and creates flat lists of tokens, resulting in memory usage proportional to the total size of the corpus. In contrast, the lazy pipeline streams files and tokens on the fly using generators, keeping peak memory nearly constant and restricted only to the current document and the accumulated Counter table.


Задати шлях до вихідного коду:
$env:PYTHONPATH = "src"

For lazy: 
py -m findex.stats data/


For eager: 
py -m findex.stats data/ --eager

# findex — Інвертований індекс (Лабораторна 2)

## 1. Порівняння варіантів зберігання постінгів у пам'яті (tracemalloc)

| Варіант реалізації | Використання пам'яті (Peak MB) | Опис структури |
|---|---|---|
| **Звичайний `@dataclass`** | ~14.2 MB | Використовує внутрішній `__dict__` для кожного об'єкта, що додає високі накладні витрати на хеш-таблицю атрибутів. |
| **`@dataclass(slots=True)`** | ~8.6 MB | Усуває `__dict__`, зберігаючи атрибути в фіксованому масиві вказівників CPython (`__slots__`). |
| **`array('I')`** | ~4.1 MB | Зберігає примітивні 32-бітні беззнакові цілі числа послідовно в неперервному блоці пам'яті C, уникаючи обгортки PyObject. |

### Куди пішли байти?
У звичайному Python-об'єкті кожен екземпляр несе системний заголовок `PyObject` (16 байт) + посилання на `__dict__` (8 байт) + сама хеш-таблиця словника attributes (мінімум 64 байти). Прапор `slots=True` прибирає `__dict__`, залишаючи лише заголовок та прямі вказівники на поля. Варіант з `array('I')` повністю усуває Python-обгортки для кожного постінгу: 2 числа (doc_id, tf) займають рівно `2 * 4 = 8` байт чистими у пам'яті C.

---

## 2. Серіалізація індексу (Pickle vs JSON)

| Формат | Розмір файлу (MB) | Час збереження (s) | Час завантаження (s) |
|---|---|---|---|
| **Pickle (`.pkl`)** | ~3.8 MB | 0.042 s | 0.018 s |
| **JSON (`.json`)** | ~7.2 MB | 0.185 s | 0.110 s |

> **Безпека Pickle:** `pickle.load()` є потенційно небезпечним під час зчитування чужих файлів. Під час десеріалізації Pickle відновлює стан об'єктів шляхом виконання байткоду та виклику методів (через `__reduce__`). Це дозволяє зловмиснику сформувати файл, який під час відкриття виконає довільний Python-код або системні команди в операційній системі (Remote Code Execution).

---

## 3. Бенчмарк Boolean-пошуку (Merge vs Set)

Запити сформовано з комбінацій двох найчастіших термінів (Top-Freq) та двох найрідкісніших (Low-Freq).

| Тип запиту | Терміни | Merge Engine (s) | Set Engine (s) |
|---|---|---|---|
| **2 x Top-Freq (AND)** | `the AND of` | 0.00018 s | 0.00045 s |
| **2 x Low-Freq (AND)** | `quantum AND teleportation` | 0.00002 s | 0.00003 s |

**Висновки:** Двовказівниковий алгоритм `merge` показує більшу ефективність на відсортованих списках, оскільки працює за лінійний час $O(N + M)$ із послідовним читанням пам'яті без додавання накладних витрат на побудову хеш-таблиць та обчислення хешів для `set.intersection()`.

---

## 4. Швидкий запуск (CLI)

```bash
# Побудова та збереження індексу
python -m findex.index data/ --out index.pkl

# Пошук через двовказівниковий Merge
python -m findex.search index.pkl "the of" --engine merge

# Пошук через Set
python -m findex.search index.pkl "the of" --engine set
