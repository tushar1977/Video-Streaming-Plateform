#!/bin/bash
set -o errexit
set -o pipefail
export FLASK_APP=myapp
export FLASK_DEBUG=True
export DB_USERNAME=root
export DB_PASSWORD=Tushar2005!
export DB_HOSTNAME=45.67.216.197
export DB_NAME=video_streaming
echo "Starting the application..."
exec gunicorn --bind 0.0.0.0:${PORT:-8000} "run:app"
