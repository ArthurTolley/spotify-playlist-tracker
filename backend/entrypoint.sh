#!/bin/sh
set -e

if [ -z "$FLASK_SECRET_KEY" ]; then
  if [ -f /data/.secret ]; then
    FLASK_SECRET_KEY=$(cat /data/.secret)
  else
    FLASK_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
    echo "$FLASK_SECRET_KEY" > /data/.secret
  fi
  export FLASK_SECRET_KEY
fi

echo "Initializing database..."
SKIP_SCHEDULER=1 python init_db.py

echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:8888 --workers 1 --threads 4 --timeout 120 app:app
