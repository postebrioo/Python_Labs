FROM python:3.11-slim

WORKDIR /app

# Копіюємо конфігурацію, вихідний код та вебшаблони
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Встановлюємо FastAPI, Uvicorn та інші вебзалежності напряму через pip
RUN pip install --no-cache-dir fastapi uvicorn pydantic pydantic-settings jinja2

# Додаємо шлях до src у PYTHONPATH, щоб Python бачив пакет findex
ENV PYTHONPATH="/app/src"

# Генеруємо мінімальний робочий індекс для сервісу під час збірки
RUN python -c "from findex.index import InvertedIndex; idx = InvertedIndex(); idx.save_pickle('index.pkl')"

ENV INDEX_PATH="index.pkl"

# Створюємо не-root користувача з міркувань безпеки
RUN useradd -m findexuser && chown -R findexuser:findexuser /app
USER findexuser

EXPOSE 8000
CMD ["uvicorn", "findex.web.app:app", "--host", "0.0.0.0", "--port", "8000"]