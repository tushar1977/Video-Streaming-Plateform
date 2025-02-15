#!/bin/bash

# Read environment variables
export SECRET=$(cat /run/secrets/SECRET)
export PORT=$(cat /run/secrets/PORT)
export DB_USERNAME=$(cat /run/secrets/DB_USERNAME)
export DB_PASSWORD=$(cat /run/secrets/DB_PASSWORD)
export DB_HOSTNAME=$(cat /run/secrets/DB_HOSTNAME)
export DB_NAME=$(cat /run/secrets/DB_NAME)
export DB_PORT=$(cat /run/secrets/DB_PORT)

# Start the application with Gunicorn
exec python3 run.py
