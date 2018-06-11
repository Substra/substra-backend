# Substrabac
Backend of the Substra platform

## Getting started

1. Clone the repo:
 ```
 git clone https://github.com/SubstraFoundation/substrabac
 ```
2. Install dependencies (might be useful to create a virtual environment before, eg using virtualenv and virtualenvwrapper):
  - For numpy, scipy, and pandas (for Unbuntu & Debian users): `sudo apt-get install python-numpy python-scipy python-pandas`
  - `pip install -r requirements.txt`
3. Setup the database: 
  - Install [PostgreSQL](https://www.postgresql.org/download/) if needed
  - [Create a database](https://www.postgresql.org/docs/10/static/tutorial-createdb.html).
4. Create the database and user with password (default parameters are described in `settings/dev.py`)
  ```
  $> dropdb substrabac
  $> createdb -E UTF8 substrabac
  $> sudo su postgres
  $> psql
  $ CREATE USER substrabac WITH PASSWORD 'substrabac' CREATEDB CREATEROLE SUPERUSER
  
```
5. Run migrations: `python manage.py migrate`
6. Create a superuser: `python manage.py createsuperuser`

## Get substra-network conf

Run the `get_conf_from_network.py` script for getting generated files from the substra-network and being able to interact with it.

```
python get_conf_from_network.py
```
It will populate the `substrapp/conf` folder.

## Launch the server

Run the server locally: `python manage.py runserver`.

## Testing with the browsable API

For displaying data in a web browser, you will have to override your headers, especially the Accept header for specifiying the version.
You can use the modheader extension available [here for Chrome](https://chrome.google.com/webstore/detail/modheader/idgpnmonknjnojddfkpgkljpfnnfcklj) and [here for Firefox](https://addons.mozilla.org/en-US/firefox/addon/modheader-firefox/):

You can then configure it like that:
![](assets/modheader_config.png) 

Now you can reach http://localhost:8000/ :tada: