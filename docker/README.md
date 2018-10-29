Use classical docker-compose command in the root directory of this repository with `-f` and ` --project-directory` options.

For instance, `up -d`:

``` docker-compose -f docker/docker-compose.yaml --project-directory . up -d ```

To test from scratch, you may have to remove the `postgres-data/` directory in the root directory of this repository.
