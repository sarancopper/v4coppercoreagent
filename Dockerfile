# v4coppercoreagent/Dockerfile

FROM python:3.12.1-slim

# 1. Install system dependencies required for mysqlclient

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    pkg-config \
    default-libmysqlclient-dev \
    default-mysql-client \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy the rest of your source code
COPY src/ src/
# COPY .env .env  # If you want to copy local .env (careful with secrets in production)

# 4. Expose port 8000 for FastAPI
EXPOSE 8000

# 5. (Optional) Environment variables
ENV PYTHONUNBUFFERED=1

# 6. Default command to run FastAPI
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
