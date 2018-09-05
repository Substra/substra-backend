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
4. Create a main postgresql use with passwordr:
  ```shell
  $> sudo su postgres
  $> psql
  $ CREATE USER substrabac WITH PASSWORD 'substrabac' CREATEDB CREATEROLE SUPERUSER;
  ```
5. Create two databases for both orgs: owkin and chu-nantes. A shell script is available, do not hesitate to run it.
It will drop the databases if they are already created, then create them and grant all privileges to your main user substrabac.
 (If this is the first time you create the databases, you will see some warnings which are pointless):

  ```shell
  $> ./substrabac/scripts/recreate_db.sh 
```
6. Do not run django migrations on these database, as we will populate them from psql dump relative to the data already set in the ledger thanks to the run docker instance of the substra-network:
```shell
  $> ./substrabac/scripts/load_fixtures.sh 
```
It will populate the databases and create the `owkin` and `chu-nantes` folders in the `medias` folder.
7. Create a superuser: `python substrabac/manage.py createsuperuser`

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

### Launch celery workers

Execute this command in the `substrabac/substrabac` folder.

Note the use of the development settings. 

```shell
DJANGO_SETTINGS_MODULE=substrabac.settings.dev.owkin celery -E -A substrabac worker -l info -B -n owkin
DJANGO_SETTINGS_MODULE=substrabac.settings.dev.chunantes celery -E -A substrabac worker -l info -B -n chunantes
```

## Launch the servers

Go in the `substrabac` folder and run the server locally:
 ```
 python manage.py runserver 8000 --settings=substrabac.settings.dev.owkin
 python manage.py runserver 8001 --settings=substrabac.settings.dev.chunantes
 ```
 Note that you should run them NOT at the same time as we do not set different host and port right now.
 These celery workers have periodic task with a 10 sec period.
 
## Test by creating a traintuple 

You can test your environment by crating a traintuple: 
```shell
curl -H "Accept: text/html;version=0.0, */*;version=0.0" -H "Content-Type: application/json" -d '{"algo_key":"ae5f5c5762e7ffbdfd5bf3a167629a142496195955f6d9a1a8853645dc7e1bf3","model_key":"10060f1d9e450d98bb5892190860eee8dd48594f00e0e1c9374a27c5acdba568","train_data_keys":["62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a","42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9"]}' -X POST http://localhost:8001/traintuple/?format=json
```
It will try to create a traintuple with creator: chu-nantes (localhost:8001).
The chu-nantes celery worker will try to add the traintuple to the ledger.
You can check your traintuple has been corectly added by visiting `http://localhost:8000/traintuple/` or `http://localhost:8001/traintuple/`
As the trainData passed are also created by chu-nantes, the chu-nantes celery worker will try to update the traintuple status to `training` and save some data if needed.
You can check `http://localhost:8000/traintuple/` or `http://localhost:8001/traintuple/` to check if the status of your newly created traintuple is set to `training` after 10 sec (celery worker periodic task period).
You can also check a new challenge has been added in `medias/chu-nantes` with a `metrics.py` file but not `description.md` file.

## Testing with the browsable API

For displaying data in a web browser, you will have to override your headers, especially the Accept header for specifiying the version.
You can use the modheader extension available [here for Chrome](https://chrome.google.com/webstore/detail/modheader/idgpnmonknjnojddfkpgkljpfnnfcklj) and [here for Firefox](https://addons.mozilla.org/en-US/firefox/addon/modheader-firefox/):

You can then configure it like that:  
![](assets/modheader_config.png) 

Now you can reach `http://localhost:8000/` and `http://localhost:8001/` :tada:

## Version

You will note substrabac use a versioned REST API with the header protocol.
Current is `0.0`.

## Miscelaneous

If you are using pycharm, you can very easily automate your servers and celery workers run configuration.

Use these configurations for easier debugging and productivity:

![](assets/conf.png)
![](assets/server_owkin.png)
![](assets/server_chunantes.png) 
![](assets/celery_owkin.png) 
![](assets/celery_chunantes.png) 

Do not hesitate to put breakpoints in your code. Even with periodic celery tasks and hit the `bug` button for launching your pre configurations.

You can even access directly to the databases (password is `substrabac` as described in the beginning of this document):
![](assets/database_owkin.png) 
![](assets/database_owkin_challenges.png) 

## License

This project is developed under the Apache License, Version 2.0 (Apache-2.0), located in the [LICENSE](./LICENSE) file.

