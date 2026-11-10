FROM python:3.11-slim

WORKDIR /app

# Копіюємо конфігурацію проєкту та вихідний код
COPY pyproject.toml ./
COPY src/ ./src/
COPY index.pkl ./index.pkl

# Встановлюємо пакет і всі залежності через звичайний pip
RUN pip install --no-cache-dir .

ENV INDEX_PATH="index.pkl"

# З міркувань безпеки створюємо не-root користувача
RUN useradd -m findexuser && chown -R findexuser:findexuser /app
USER findexuser

EXPOSE 8000
CMD ["uvicorn", "findex.web.app:app", "--host", "0.0.0.0", "--port", "8000"]