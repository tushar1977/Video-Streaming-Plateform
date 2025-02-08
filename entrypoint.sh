#!/bin/bash

# Read environment variables
export SECRET="${SECRET}"
export PORT="${PORT}"
export DB_USERNAME="${DB_USERNAME}"
export DB_PASSWORD="${DB_PASSWORD}"
export DB_HOSTNAME="${DB_HOSTNAME}"
export DB_NAME="${DB_NAME}"
export DB_PORT="${DB_PORT}"

# Start the application
exec gunicorn --bind "0.0.0.0:$PORT" "run:app"
