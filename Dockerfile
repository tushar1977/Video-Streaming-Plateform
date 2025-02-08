FROM python:3.8-slim-buster
RUN apt-get update && apt-get install ffmpeg -y && apt-get install -y \
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
ENV FLASK_APP=myapp
EXPOSE 8100
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]
