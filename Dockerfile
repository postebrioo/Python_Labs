FROM python:3.11-slim

WORKDIR /app

# Копіюємо лише те, що гарантовано є на GitHub
COPY pyproject.toml ./
COPY src/ ./src/

# Встановлюємо пакет через pip
RUN pip install --no-cache-dir .

# Створюємо мінімальний робочий файл index.pkl прямо під час збірки, щоб додаток не падаль
RUN python -c "from findex.index import InvertedIndex; idx = InvertedIndex(); idx.save_pickle('index.pkl')"

ENV INDEX_PATH="index.pkl"

# Створюємо не-root користувача для безпеки
RUN useradd -m findexuser && chown -R findexuser:findexuser /app
USER findexuser

EXPOSE 8000
CMD ["uvicorn", "findex.web.app:app", "--host", "0.0.0.0", "--port", "8000"]