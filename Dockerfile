FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml requirements.txt ./
COPY app ./app
COPY ui ./ui
COPY data ./data
COPY eval ./eval
RUN pip install --no-cache-dir -e ".[dev]"
EXPOSE 8000
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
