FROM python:3.11-slim

WORKDIR /app

# Копіюємо весь проєкт включно з папкою src
COPY pyproject.toml ./
COPY src/ ./src/

# Встановлюємо PYTHONPATH, щоб Python одразу бачив вміст папки src
ENV PYTHONPATH="/app/src"

# Встановлюємо вебзалежності
RUN pip install --no-cache-dir fastapi uvicorn pydantic pydantic-settings jinja2

# Генеруємо мінімальний робочий індекс для сервісу
RUN python -c "from findex.index import InvertedIndex; idx = InvertedIndex(); idx.save_pickle('index.pkl')"

ENV INDEX_PATH="index.pkl"

# Створюємо не-root користувача для безпеки
RUN useradd -m findexuser && chown -R findexuser:findexuser /app
USER findexuser

EXPOSE 8000
CMD ["uvicorn", "findex.web.app:app", "--host", "0.0.0.0", "--port", "8000"]