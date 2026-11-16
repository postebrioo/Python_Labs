FROM python:3.11-slim

WORKDIR /app

# Копіюємо конфігурацію, файли проєкту та вихідний код
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Встановлюємо пакет у режимі редагування, щоб Python бачив findex з будь-якого місця
RUN pip install --no-cache-dir . fastapi uvicorn pydantic pydantic-settings jinja2

# Генеруємо мінімальний робочий індекс для сервісу під час збірки
RUN python -c "from findex.index import InvertedIndex; idx = InvertedIndex(); idx.save_pickle('index.pkl')"

ENV INDEX_PATH="index.pkl"

# Створюємо не-root користувача з міркувань безпеки
RUN useradd -m findexuser && chown -R findexuser:findexuser /app
USER findexuser

EXPOSE 8000
CMD ["uvicorn", "findex.web.app:app", "--host", "0.0.0.0", "--port", "8000"]