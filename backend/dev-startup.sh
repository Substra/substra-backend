#!/bin/sh
python manage.py migrate
python manage.py add_user org-1 p@sswr0d44 mychannel
python manage.py generate_fixtures
python manage.py runserver 0.0.0.0:8000
