#!/bin/bash

# Define variables
DB_NAME="austindb"
BACKUP_DIR="./dbbackup"
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_backup_$TIMESTAMP.sql"

# Ensure backup directory exists
mkdir -p $BACKUP_DIR

echo "Pulling latest changes from GitHub..."
git pull origin main

echo "Activating virtual environment..."
source ./venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Backing up the database..."
if pg_dump $DB_NAME > $BACKUP_FILE; then
    echo "Database backup successful: $BACKUP_FILE"
else
    echo "Error: Database backup failed!"
    exit 1
fi

echo "Generating migrations..."
python manage.py makemigrations

echo "Applying database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Restarting Gunicorn..."
sudo systemctl restart gunicorn

echo "Reloading Nginx (if needed)..."
sudo nginx -t && sudo systemctl reload nginx

echo "Deployment complete!"
