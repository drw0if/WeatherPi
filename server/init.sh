#!/bin/sh

# Check if db exists
if [ ! -f "db/database.db" ]; then
    echo "Database not found, creating..."
    python3 db.py
else
    echo "Database found."
fi

gunicorn -b 0.0.0.0:80 app:app