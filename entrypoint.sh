#!/bin/bash

# Exit on error
set -e

echo "=========================================="
echo "Starting Django Education System"
echo "=========================================="

# Wait for database (if using PostgreSQL)
# if [ "$DATABASE_URL" != "" ]; then
#     echo "Waiting for database..."
#     while ! nc -z db 5432; do
#       sleep 0.5
#     done
#     echo "Database is ready!"
# fi

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if it doesn't exist (optional)
# echo "Creating superuser if not exists..."
# echo "from accounts.models import User; User.objects.filter(email='admin@example.com').exists() or User.objects.create_superuser('admin@example.com', 'admin', 'password')" | python manage.py shell

# Start the application
echo "Starting application..."
exec "$@"
