# Test migrations

Generate test data on main branch

```
git checkout main && git pull
make install  # install python dependencies
make quickstart  # wait for db, run migrations, create a user, start the server
make fixtures  # generate assets fixtures
```

Test migration files

```
git checkout feature_branch
python backend/manage.py migrate --settings backend.settings.test
```
