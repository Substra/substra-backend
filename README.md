# substrabac
Backend of the Substra platform

## Getting started

1. Clone the repo: `git clone `
2. Install dependencies (might be useful to create a virtual environment before, eg using virtualenv and virtualenvwrapper):
  - For numpy, scipy, and pandas (for Unbuntu & Debian users): `sudo apt-get install python-numpy python-scipy python-pandas`
  - `pip install -r requirements.txt`
3. Setup the database: 
  - Install [PostgreSQL](https://www.postgresql.org/download/) if needed
  - [Create a database](https://www.postgresql.org/docs/10/static/tutorial-createdb.html).
4. Define environment variables:
  - `SUBSTRA_DB_NAME`: name of the database
  - `SUBSTRA_DB_USER`: owner of the database
  - `SUBSTRA_DB_PWD`: owner password
5. Run migrations: `python manage.py migrate`
6. Create a superuser: `python manage.py createsuperuser`
7. Run the server locally: `python manage.py runserver`

## Run the app with docker-compose

:warning: TODO
