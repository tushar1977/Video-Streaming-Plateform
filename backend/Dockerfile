FROM python:3.11-slim

WORKDIR /app

RUN mkdir -p /.certs

COPY req.txt .

RUN pip install --no-cache-dir -r req.txt

COPY . .

EXPOSE 3000

CMD ["python", "run.py"]
