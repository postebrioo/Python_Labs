FROM python:3.11-slim

WORKDIR /app

# Копіюємо конфігурацію та вихідний код
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Встановлюємо пакет та необхідні бібліотеки через pip
RUN pip install --no-cache-dir . fastapi uvicorn pydantic pydantic-settings jinja2

# Переходимо всередину папки src, щоб python/uvicorn бачив пакет findex напряму
WORKDIR /app/src

# Генеруємо мінімальний робочий індекс для сервісу
RUN python -c "from findex.index import InvertedIndex; idx = InvertedIndex(); idx.save_pickle('/app/index.pkl')"

ENV INDEX_PATH="/app/index.pkl"

# Створюємо не-root користувача для безпеки та даємо йому права на всю папку /app
RUN useradd -m findexuser && chown -R findexuser:findexuser /app
USER findexuser

EXPOSE 8000
CMD ["uvicorn", "findex.web.app:app", "--host", "0.0.0.0", "--port", "8000"]