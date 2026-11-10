FROM python:3.11-slim

WORKDIR /app

# Копіюємо конфігурацію та вихідний код
COPY pyproject.toml ./
COPY src/ ./src/

# Встановлюємо шлях до вихідного коду, щоб Python бачив пакет findex
ENV PYTHONPATH=/app/src

# Встановлюємо необхідні вебзалежності напряму
RUN pip install --no-cache-dir fastapi uvicorn pydantic pydantic-settings jinja2

# Створюємо мінімальний робочий файл index.pkl під час збірки
RUN python -c "from findex.index import InvertedIndex; idx = InvertedIndex(); idx.save_pickle('index.pkl')"

ENV INDEX_PATH="index.pkl"

# Створюємо не-root користувача для безпеки
RUN useradd -m findexuser && chown -R findexuser:findexuser /app
USER findexuser

EXPOSE 8000
CMD ["uvicorn", "findex.web.app:app", "--host", "0.0.0.0", "--port", "8000"]