#!/bin/sh
echo "Start create migrations"
python manage.py makemigrations
echo "Start migrate"
python manage.py migrate
echo "Start wsgi"
#gunicorn yatube.wsgi:application --bind 0.0.0.0:8000
gunicorn yatube.wsgi:application --bind 0.0.0.0:8000 --error-logfile /code/logs/gunicorn.error.log --access-logfile /code/logs/gunicorn.access.log --capture-output --log-level debug
exec "$@"