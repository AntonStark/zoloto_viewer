web: gunicorn zoloto_viewer.config.wsgi:application --bind 0.0.0.0:$PORT
release: python manage.py migrate
worker: python manage.py process_tasks