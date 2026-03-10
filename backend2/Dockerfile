FROM python:3.9-slim AS builder

WORKDIR /install

COPY req.txt .

RUN pip install --upgrade pip \
 && pip install --prefix=/install --no-cache-dir -r req.txt


FROM python:3.9-slim

WORKDIR /app

# Copy installed packages only
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

EXPOSE 3002

CMD ["python", "run.py"]
