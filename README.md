# Substrabac
Backend of the Substra platform

## Getting started 1: Prepare the django app

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
5. Run migrations: `python substrabac/manage.py migrate`
6. Create a superuser: `python substrabac/manage.py createsuperuser`

## Getting started 2: Linking the app with Hyperledger Fabric

### Get Fabric binaries

Run `./boostrap.sh`

### Get substra-network conf

Run the `get_conf_from_network.py` script for getting generated files from the substra-network and being able to interact with it.  
:warning: The `substra-network` directory (cloned from [here](https://github.com/SubstraFoundation/substra-network)) should be located at the same level as the `substrabac` project directory.

```
python substrabac/get_conf_from_network.py
```
It will populate the `substrabac/substrapp/conf` folder.
 
### Make the subtra-network available to the app

[See here](https://github.com/SubstraFoundation/substra-network#network).  

### Install rabbitmq

```shell
sudo apt-get install rabbitmq-server
```

### Launch celery worker

Execute this command in the `substrabac/substrabac` folder.

Note the use of the development settings. 

```shell
DJANGO_SETTINGS_MODULE=substrabac.settings.dev celery -E -A substrabac worker -l info
```

## Launch the server

Go in the `substrabac` folder and run the server locally: `python manage.py runserver`.

## Testing with the browsable API

For displaying data in a web browser, you will have to override your headers, especially the Accept header for specifiying the version.
You can use the modheader extension available [here for Chrome](https://chrome.google.com/webstore/detail/modheader/idgpnmonknjnojddfkpgkljpfnnfcklj) and [here for Firefox](https://addons.mozilla.org/en-US/firefox/addon/modheader-firefox/):

You can then configure it like that:  
![](assets/modheader_config.png) 

Now you can reach http://localhost:8000/ :tada:

## License

This project is developed under the Apache License, Version 2.0 (Apache-2.0), located in the [LICENSE](./LICENSE) file.