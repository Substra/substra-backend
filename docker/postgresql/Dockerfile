FROM library/postgres:10.5
ENV POSTGRES_USER substrabac
ENV USER substrabac
ENV POSTGRES_PASSWORD substrabac
ENV POSTGRES_DB substrabac

COPY ./substrabac/scripts /usr/src/scripts
COPY ./docker/postgresql/init.sh /docker-entrypoint-initdb.d/
