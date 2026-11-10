FROM python:3.11-slim

WORKDIR /app

# Копіюємо конфігурацію та вихідний код разом із корпусом даних
COPY pyproject.toml ./
COPY src/ ./src/
COPY data/ ./data/

# Встановлюємо пакет через pip
RUN pip install --no-cache-dir .

# Генеруємо файл індексу прямо всередині контейнера при збірці
RUN python -m findex.cli index data/ --out index.pkl --positions

ENV INDEX_PATH="index.pkl"

# Створюємо не-root користувача для безпеки
RUN useradd -m findexuser && chown -R findexuser:findexuser /app
USER findexuser

EXPOSE 8000
CMD ["uvicorn", "findex.web.app:app", "--host", "0.0.0.0", "--port", "8000"]