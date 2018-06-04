#!/bin/bash

dropdb substrabac
createdb -E UTF8 substrabac
psql -d substrabac -c "GRANT ALL PRIVILEGES ON DATABASE substrabac to substrabac;"
