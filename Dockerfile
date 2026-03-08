FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
COPY find_location.py .

RUN pip install --no-cache-dir .

ENTRYPOINT ["python", "-m", "spark_mcp"]
