import os
import json
import glob
import argparse

from subprocess import call, check_output

dir_path = os.path.dirname(os.path.realpath(__file__))
raven_dryrunner_url = "https://a1c2de65bb0f4120aa11d75bca9b47f6@sentry.io/1402760"
raven_worker_url = "https://76abd6b5d11e48ea8a118831c86fc615@sentry.io/1402762"
raven_scheduler_url = raven_worker_url

FABRIC_LOGGING_SPEC = "debug"


BACKEND_PORT = {
    'owkin': 8000,
    'chunantes': 8001,
    'clb': 8002
}


def generate_docker_compose_file(conf, launch_settings):

    # POSTGRES
    POSTGRES_USER = 'substrabac'
    USER = 'substrabac'
    POSTGRES_PASSWORD = 'substrabac'
    POSTGRES_DB = 'substrabac'

    # RABBITMQ
    RABBITMQ_DEFAULT_USER = 'guest'
    RABBITMQ_DEFAULT_PASS = 'guest'
    RABBITMQ_HOSTNAME = 'rabbitmq'
    RABBITMQ_NODENAME = 'rabbitmq'
    RABBITMQ_DOMAIN = 'rabbit'
    RABBITMQ_PORT = '5672'

    # CELERY
    CELERY_BROKER_URL = f'amqp://{RABBITMQ_DEFAULT_USER}:{RABBITMQ_DEFAULT_PASS}@{RABBITMQ_DOMAIN}:{RABBITMQ_PORT}//'

    try:
        from ruamel import yaml
    except ImportError:
        import yaml

    # Docker compose config
    docker_compose = {'substrabac_services': {},
                      'substrabac_tools': {'postgresql': {'container_name': 'postgresql',
                                                          'image': 'library/postgres:10.5',
                                                          'restart': 'unless-stopped',
                                                          'logging': {'driver': 'json-file', 'options': {'max-size': '20m', 'max-file': '5'}},
                                                          'environment': [f'POSTGRES_USER={POSTGRES_USER}',
                                                                          f'USER={USER}',
                                                                          f'POSTGRES_PASSWORD={POSTGRES_PASSWORD}',
                                                                          f'POSTGRES_DB={POSTGRES_DB}'],
                                                          'volumes': [
                                                              '/substra/backup/postgres-data:/var/lib/postgresql/data',
                                                              f'{dir_path}/postgresql/init.sh:/docker-entrypoint-initdb.d/init.sh'],
                                                          },
                                           'celerybeat': {'container_name': 'celerybeat',
                                                          'hostname': 'celerybeat',
                                                          'image': 'substra/celerybeat',
                                                          'restart': 'unless-stopped',
                                                          'command': '/bin/bash -c "while ! { nc -z rabbit 5672 2>&1; }; do sleep 1; done; while ! { nc -z postgresql 5432 2>&1; }; do sleep 1; done; celery -A substrabac beat -l info"',
                                                          'logging': {'driver': 'json-file', 'options': {'max-size': '20m', 'max-file': '5'}},
                                                          'environment': ['PYTHONUNBUFFERED=1',
                                                                          f'CELERY_BROKER_URL={CELERY_BROKER_URL}',
                                                                          f'DJANGO_SETTINGS_MODULE=substrabac.settings.common'],
                                                          'depends_on': ['postgresql', 'rabbit']
                                                          },
                                           'rabbit': {'container_name': 'rabbit',
                                                      'hostname': 'rabbitmq',     # Must be set to be able to recover from volume
                                                      'restart': 'unless-stopped',
                                                      'image': 'rabbitmq:3',
                                                      'logging': {'driver': 'json-file', 'options': {'max-size': '20m', 'max-file': '5'}},
                                                      'environment': [f'RABBITMQ_DEFAULT_USER={RABBITMQ_DEFAULT_USER}',
                                                                      f'RABBITMQ_DEFAULT_PASS={RABBITMQ_DEFAULT_PASS}',
                                                                      f'HOSTNAME={RABBITMQ_HOSTNAME}',
                                                                      f'RABBITMQ_NODENAME={RABBITMQ_NODENAME}'],
                                                      'volumes': ['/substra/backup/rabbit-data:/var/lib/rabbitmq']
                                                      },
                                           },
                      'path': os.path.join(dir_path, './docker-compose-dynamic.yaml')}

    for org in conf:
        org_name = org['name']
        orderer_ca = org['orderer']['ca']
        peer = org['peer']['name']
        org_name_stripped = org_name.replace('-', '')

        port = BACKEND_PORT[org_name_stripped]

        cpu_count = os.cpu_count()
        processes = 2 * int(cpu_count) + 1

        if launch_settings == 'prod':
            django_server = f'python3 manage.py collectstatic --noinput; uwsgi --http :{port} --module substrabac.wsgi --static-map /static=/usr/src/app/substrabac/statics --master --processes {processes} --threads 2'
        else:

            django_server = f'python3 manage.py runserver 0.0.0.0:{port}'

        backend = {'container_name': f'{org_name_stripped}.substrabac',
                   'image': 'substra/substrabac',
                   'restart': 'unless-stopped',
                   'ports': [f'{port}:{port}'],
                   'command': f'/bin/bash -c "while ! {{ nc -z postgresql 5432 2>&1; }}; do sleep 1; done; yes | python manage.py migrate; {django_server}"',
                   'logging': {'driver': 'json-file', 'options': {'max-size': '20m', 'max-file': '5'}},
                   'environment': ['DATABASE_HOST=postgresql',
                                   'SUBSTRABAC_PEER_PORT=internal',
                                   f'CELERY_BROKER_URL={CELERY_BROKER_URL}',
                                   f'SUBSTRABAC_ORG={org_name}',
                                   f'SUBSTRABAC_DEFAULT_PORT={port}',
                                   f'DJANGO_SETTINGS_MODULE=substrabac.settings.{launch_settings}',
                                   'PYTHONUNBUFFERED=1',
                                   f"BACK_AUTH_USER={os.environ.get('BACK_AUTH_USER', '')}",
                                   f"BACK_AUTH_PASSWORD={os.environ.get('BACK_AUTH_PASSWORD', '')}",
                                   f"SITE_HOST={os.environ.get('SITE_HOST', 'localhost')}",
                                   f"SITE_PORT={os.environ.get('BACK_PORT', 9000)}",
                                   f"FABRIC_CFG_PATH_ENV={org['peer']['docker_core_dir']}",
                                   f"CORE_PEER_ADDRESS_ENV={org['peer']['host']}:{org['peer']['port']['internal']}",
                                   f"FABRIC_LOGGING_SPEC={FABRIC_LOGGING_SPEC}"],
                   'volumes': ['/substra/medias:/substra/medias',
                               '/substra/servermedias:/substra/servermedias',
                               '/substra/dryrun:/substra/dryrun',
                               '/substra/static:/usr/src/app/substrabac/statics',
                               f'/substra/conf/{org_name}:/substra/conf/{org_name}',
                               f'{orderer_ca}:{orderer_ca}',
                               f'/substra/data/orgs/{org_name}/ca-cert.pem:/substra/data/orgs/{org_name}/ca-cert.pem',
                               f'{org["core_peer_mspconfigpath"]}:{org["core_peer_mspconfigpath"]}',
                               f'/substra/data/orgs/{org_name}/tls/{peer}:/substra/data/orgs/{org_name}/tls/{peer}',
                               ],
                   'depends_on': ['postgresql', 'rabbit']}

        scheduler = {'container_name': f'{org_name_stripped}.scheduler',
                     'hostname': f'{org_name}.scheduler',
                     'image': 'substra/celeryworker',
                     'restart': 'unless-stopped',
                     'command': f'/bin/bash -c "while ! {{ nc -z rabbit 5672 2>&1; }}; do sleep 1; done; while ! {{ nc -z postgresql 5432 2>&1; }}; do sleep 1; done; celery -A substrabac worker -l info -n {org_name_stripped} -Q {org_name},scheduler,celery --hostname {org_name}.scheduler"',
                     'logging': {'driver': 'json-file', 'options': {'max-size': '20m', 'max-file': '5'}},
                     'environment': [f'ORG={org_name_stripped}',
                                     f'SUBSTRABAC_ORG={org_name}',
                                     f'SUBSTRABAC_DEFAULT_PORT={port}',
                                     'SUBSTRABAC_PEER_PORT=internal',
                                     f'CELERY_BROKER_URL={CELERY_BROKER_URL}',
                                     f'DJANGO_SETTINGS_MODULE=substrabac.settings.{launch_settings}',
                                     'PYTHONUNBUFFERED=1',
                                     f"BACK_AUTH_USER={os.environ.get('BACK_AUTH_USER', '')}",
                                     f"BACK_AUTH_PASSWORD={os.environ.get('BACK_AUTH_PASSWORD', '')}",
                                     f"SITE_HOST={os.environ.get('SITE_HOST', 'localhost')}",
                                     f"SITE_PORT={os.environ.get('BACK_PORT', 9000)}",
                                     'DATABASE_HOST=postgresql',
                                     f"FABRIC_CFG_PATH_ENV={org['peer']['docker_core_dir']}",
                                     f"CORE_PEER_ADDRESS_ENV={org['peer']['host']}:{org['peer']['port']['internal']}",
                                     f"FABRIC_LOGGING_SPEC={FABRIC_LOGGING_SPEC}"],
                     'volumes': [f'/substra/conf/{org_name}:/substra/conf/{org_name}',
                                 f'{orderer_ca}:{orderer_ca}',
                                 f'/substra/data/orgs/{org_name}/ca-cert.pem:/substra/data/orgs/{org_name}/ca-cert.pem',
                                 f'{org["core_peer_mspconfigpath"]}:{org["core_peer_mspconfigpath"]}',
                                 f'/substra/data/orgs/{org_name}/tls/{peer}:/substra/data/orgs/{org_name}/tls/{peer}',
                                 ],
                     'depends_on': [f'substrabac{org_name_stripped}', 'postgresql', 'rabbit']}

        worker = {'container_name': f'{org_name_stripped}.worker',
                  'hostname': f'{org_name}.worker',
                  'image': 'substra/celeryworker',
                  'restart': 'unless-stopped',
                  'command': f'/bin/bash -c "while ! {{ nc -z rabbit 5672 2>&1; }}; do sleep 1; done; while ! {{ nc -z postgresql 5432 2>&1; }}; do sleep 1; done; celery -A substrabac worker -l info -n {org_name_stripped} -Q {org_name},{org_name}.worker,celery --hostname {org_name}.worker"',
                  'logging': {'driver': 'json-file', 'options': {'max-size': '20m', 'max-file': '5'}},
                  'environment': [f'ORG={org_name_stripped}',
                                  f'SUBSTRABAC_ORG={org_name}',
                                  f'SUBSTRABAC_DEFAULT_PORT={port}',
                                  'SUBSTRABAC_PEER_PORT=internal',
                                  f'CELERY_BROKER_URL={CELERY_BROKER_URL}',
                                  f'DJANGO_SETTINGS_MODULE=substrabac.settings.{launch_settings}',
                                  'PYTHONUNBUFFERED=1',
                                  f"BACK_AUTH_USER={os.environ.get('BACK_AUTH_USER', '')}",
                                  f"BACK_AUTH_PASSWORD={os.environ.get('BACK_AUTH_PASSWORD', '')}",
                                  f"SITE_HOST={os.environ.get('SITE_HOST', 'localhost')}",
                                  f"SITE_PORT={os.environ.get('BACK_PORT', 9000)}",
                                  'DATABASE_HOST=postgresql',
                                  f"FABRIC_CFG_PATH_ENV={org['peer']['docker_core_dir']}",
                                  f"CORE_PEER_ADDRESS_ENV={org['peer']['host']}:{org['peer']['port']['internal']}",
                                  f"FABRIC_LOGGING_SPEC={FABRIC_LOGGING_SPEC}"],
                  'volumes': ['/var/run/docker.sock:/var/run/docker.sock',
                              '/substra/medias:/substra/medias',
                              '/substra/servermedias:/substra/servermedias',
                              f'/substra/conf/{org_name}:/substra/conf/{org_name}',
                              f'{orderer_ca}:{orderer_ca}',
                              f'/substra/data/orgs/{org_name}/ca-cert.pem:/substra/data/orgs/{org_name}/ca-cert.pem',
                              f'{org["core_peer_mspconfigpath"]}:{org["core_peer_mspconfigpath"]}',
                              f'/substra/data/orgs/{org_name}/tls/{peer}:/substra/data/orgs/{org_name}/tls/{peer}',
                              ],
                  'depends_on': [f'substrabac{org_name_stripped}', 'rabbit']}

        dryrunner = {'container_name': f'{org_name_stripped}.dryrunner',
                     'hostname': f'{org_name}.dryrunner',
                     'image': 'substra/celeryworker',
                     'restart': 'unless-stopped',
                     'command': f'/bin/bash -c "while ! {{ nc -z rabbit 5672 2>&1; }}; do sleep 1; done; while ! {{ nc -z postgresql 5432 2>&1; }}; do sleep 1; done; celery -A substrabac worker -l info -n {org_name_stripped} -Q {org_name},{org_name}.dryrunner,celery --hostname {org_name}.dryrunner"',
                     'logging': {'driver': 'json-file', 'options': {'max-size': '20m', 'max-file': '5'}},
                     'environment': [f'ORG={org_name_stripped}',
                                     f'SUBSTRABAC_ORG={org_name}',
                                     f'SUBSTRABAC_DEFAULT_PORT={port}',
                                     'SUBSTRABAC_PEER_PORT=internal',
                                     f'CELERY_BROKER_URL={CELERY_BROKER_URL}',
                                     f'DJANGO_SETTINGS_MODULE=substrabac.settings.{launch_settings}',
                                     'PYTHONUNBUFFERED=1',
                                     f"BACK_AUTH_USER={os.environ.get('BACK_AUTH_USER', '')}",
                                     f"BACK_AUTH_PASSWORD={os.environ.get('BACK_AUTH_PASSWORD', '')}",
                                     f"SITE_HOST={os.environ.get('SITE_HOST', 'localhost')}",
                                     f"SITE_PORT={os.environ.get('BACK_PORT', 9000)}",
                                     'DATABASE_HOST=postgresql',
                                     f"FABRIC_CFG_PATH_ENV={org['peer']['docker_core_dir']}",
                                     f"CORE_PEER_ADDRESS_ENV={org['peer']['host']}:{org['peer']['port']['internal']}",
                                     f"FABRIC_LOGGING_SPEC={FABRIC_LOGGING_SPEC}"],
                     'volumes': ['/var/run/docker.sock:/var/run/docker.sock',
                                 '/substra/medias:/substra/medias',
                                 '/substra/servermedias:/substra/servermedias',
                                 '/substra/dryrun:/substra/dryrun',
                                 f'/substra/conf/{org_name}:/substra/conf/{org_name}',
                                 f'{orderer_ca}:{orderer_ca}',
                                 f'/substra/data/orgs/{org_name}/ca-cert.pem:/substra/data/orgs/{org_name}/ca-cert.pem',
                                 f'{org["core_peer_mspconfigpath"]}:{org["core_peer_mspconfigpath"]}',
                                 f'/substra/data/orgs/{org_name}/tls/{peer}:/substra/data/orgs/{org_name}/tls/{peer}',
                                 ],
                     'depends_on': [f'substrabac{org_name_stripped}', 'rabbit']}

        # Check if we have nvidia docker
        if 'nvidia' in check_output(['docker', 'system', 'info', '-f', '"{{.Runtimes}}"']).decode('utf-8'):
            worker['runtime'] = 'nvidia'

        if launch_settings == 'dev':
            media_root = f'MEDIA_ROOT=/substra/medias/{org_name_stripped}'
            dryrun_root = f'DRYRUN_ROOT=/substra/dryrun/{org_name}'

            worker['environment'].append(media_root)
            dryrunner['environment'].append(media_root)
            backend['environment'].append(media_root)

            dryrunner['environment'].append(dryrun_root)
            backend['environment'].append(dryrun_root)
        else:
            default_domain = os.environ.get('SUBSTRABAC_DEFAULT_DOMAIN', '')
            if default_domain:
                backend['environment'].append(f"DEFAULT_DOMAIN={default_domain}")
                worker['environment'].append(f"DEFAULT_DOMAIN={default_domain}")
                scheduler['environment'].append(f"DEFAULT_DOMAIN={default_domain}")
                dryrunner['environment'].append(f"DEFAULT_DOMAIN={default_domain}")
            scheduler['environment'].append(f"RAVEN_URL={raven_scheduler_url}")
            worker['environment'].append(f"RAVEN_URL={raven_worker_url}")
            dryrunner['environment'].append(f"RAVEN_URL={raven_dryrunner_url}")

        docker_compose['substrabac_services']['substrabac' + org_name_stripped] = backend
        docker_compose['substrabac_services']['scheduler' + org_name_stripped] = scheduler
        docker_compose['substrabac_services']['worker' + org_name_stripped] = worker
        docker_compose['substrabac_services']['dryrunner' + org_name_stripped] = dryrunner
    # Create all services along to conf

    COMPOSITION = {'services': {}, 'version': '2.3', 'networks': {'default': {'external': {'name': 'net_substra'}}}}

    for name, dconfig in docker_compose['substrabac_services'].items():
        COMPOSITION['services'][name] = dconfig

    for name, dconfig in docker_compose['substrabac_tools'].items():
        COMPOSITION['services'][name] = dconfig

    with open(docker_compose['path'], 'w+') as f:
        f.write(yaml.dump(COMPOSITION, default_flow_style=False, indent=4, line_break=None))

    return docker_compose


def stop(docker_compose=None):
    print('stopping container', flush=True)

    if docker_compose is not None:
        call(['docker-compose', '-f', docker_compose['path'], '--project-directory',
              os.path.join(dir_path, '../'), 'down', '--remove-orphans'])
    else:
        call(['docker-compose', '-f', os.path.join(dir_path, './docker-compose.yaml'), '--project-directory',
              os.path.join(dir_path, '../'), 'down', '--remove-orphans'])


def start(conf, launch_settings, no_backup):
    print('Generate docker-compose file\n')
    docker_compose = generate_docker_compose_file(conf, launch_settings)

    stop(docker_compose)

    if no_backup:
        print('Clean medias directory\n')
        call(['sh', os.path.join(dir_path, '../substrabac/scripts/clean_media.sh')])
        print('Remove postgresql database\n')
        call(['rm', '-rf', '/substra/backup/postgres-data'])
        print('Remove rabbit database\n')
        call(['rm', '-rf', '/substra/backup/rabbit-data'])

    print('start docker-compose', flush=True)
    call(['docker-compose', '-f', docker_compose['path'], '--project-directory',
          os.path.join(dir_path, '../'), 'up', '-d', '--remove-orphans', '--build'])
    call(['docker', 'ps', '-a'])


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dev', action='store_true', default=False,
                        help="use dev settings")
    parser.add_argument('--no-backup', action='store_true', default=False,
                        help="Remove backup binded volume, medias and db data. Launch from scratch")
    args = vars(parser.parse_args())

    if args['dev']:
        launch_settings = 'dev'
    else:
        launch_settings = 'prod'

    no_backup = args['no_backup']

    conf = [json.load(open(file_path, 'r')) for file_path in glob.glob('/substra/conf/*/substrabac/conf.json')]

    print('Build substrabac for : ', flush=True)
    print('  Organizations :', flush=True)
    for org in conf:
        print('   -', org['name'], flush=True)

    print('', flush=True)

    start(conf, launch_settings, no_backup)
