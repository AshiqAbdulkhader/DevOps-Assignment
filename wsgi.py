"""WSGI entrypoint: `flask --app wsgi run` or `python -m gunicorn wsgi:app`."""

from aceest import create_app

app = create_app()
