release: flask db upgrade
web: gunicorn --config gunicorn.conf.py wsgi:app
worker: celery -A app.celery_app worker --loglevel=info
beat: celery -A app.celery_app beat --loglevel=info
