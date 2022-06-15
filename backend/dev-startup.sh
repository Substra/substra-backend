#!/bin/sh

python manage.py check --database default 2>/dev/null
while [ $? -eq 1 ]
do
    echo "DB not ready, waiting and retrying..."
    sleep 5
    python manage.py check --database default 2>/dev/null
done
python manage.py migrate
python manage.py add_user org-1 p@sswr0d44 mychannel
python manage.py runserver 0.0.0.0:8000
