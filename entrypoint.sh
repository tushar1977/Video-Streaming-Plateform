#!/bin/bash

exec gunicorn --certfile=/cert/cert.pem --keyfile=/key/key.pem \
  --worker-class eventlet -w 3 \
  -b 0.0.0.0:$PORT run:app
