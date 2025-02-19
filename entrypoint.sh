#!/bin/bash

exec gunicorn --certfile=/app/tls/cert.pem --keyfile=/app/tls/key.pem \
  --worker-class eventlet -w 1 \
  -b 0.0.0.0:$PORT run:app
