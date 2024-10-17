FROM python:3.8-slim-buster
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    pkg-config \
    build-essential \
    libmariadb-dev-compat \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8100

ENV FLASK_APP=myapp \
    FLASK_ENV=production \
    DB_USERNAME=root \
    DB_PASSWORD=Tushar2005! \
    DB_HOSTNAME=45.67.216.197 \
    DB_NAME=video_streaming \
    PORT=8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"]
