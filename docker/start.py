import os
import json
import glob
import argparse

from subprocess import call, check_output

dir_path = os.path.dirname(os.path.realpath(__file__))
raven_backend_url = "https://cff352ba26fc49f19e01692db93bf951@sentry.io/1317743"
raven_worker_url = "https://76abd6b5d11e48ea8a118831c86fc615@sentry.io/1402762"
raven_scheduler_url = raven_worker_url

FABRIC_LOGGING_SPEC = "debug"


BACKEND_PORT = {
    'owkin': 8000,
    'chunantes': 8001,
    'clb': 8002
}

SUBSTRA_FOLDER = os.getenv('SUBSTRA_PATH', '/substra')


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

    wait_rabbit = f'while ! {{ nc -z {RABBITMQ_DOMAIN} {RABBITMQ_PORT} 2>&1; }}; do sleep 1; done'
    wait_psql = 'while ! { nc -z postgresql 5432 2>&1; }; do sleep 1; done'

    # Docker compose config
    docker_compose = {
        'substrabac_services': {},
        'substrabac_tools': {
            'postgresql': {
                'container_name': 'postgresql',
                'labels': ['substra'],
                'image': 'substra/postgresql',
                'restart': 'unless-stopped',
                'logging': {'driver': 'json-file', 'options': {'max-size': '20m', 'max-file': '5'}},
                'environment': [
                    f'POSTGRES_USER={POSTGRES_USER}',
                    f'USER={USER}',
                    f'POSTGRES_PASSWORD={POSTGRES_PASSWORD}',
                    f'POSTGRES_DB={POSTGRES_DB}'],
                'volumes': [
                    f'{SUBSTRA_FOLDER}/backup/postgres-data:/var/lib/postgresql/data'],
            },
            'celerybeat': {
                'container_name': 'celerybeat',
                'labels': ['substra'],
                'hostname': 'celerybeat',
                'image': 'substra/celerybeat',
                'restart': 'unless-stopped',
                'command': f'/bin/bash -c "{wait_rabbit}; {wait_psql}; '
                           'celery -A substrabac beat -l info"',
                'logging': {'driver': 'json-file', 'options': {'max-size': '20m', 'max-file': '5'}},
                'environment': [
                    'PYTHONUNBUFFERED=1',
                    f'CELERY_BROKER_URL={CELERY_BROKER_URL}',
                    f'DJANGO_SETTINGS_MODULE=substrabac.settings.common'],
                'depends_on': ['postgresql', 'rabbit']
            },
            'rabbit': {
                'container_name': 'rabbit',
                'labels': ['substra'],
                'hostname': 'rabbitmq',     # Must be set to be able to recover from volume
                'restart': 'unless-stopped',
                'image': 'rabbitmq:3-management',
                'logging': {'driver': 'json-file', 'options': {'max-size': '20m', 'max-file': '5'}},
                'environment': [
                    f'RABBITMQ_DEFAULT_USER={RABBITMQ_DEFAULT_USER}',
                    f'RABBITMQ_DEFAULT_PASS={RABBITMQ_DEFAULT_PASS}',
                    f'HOSTNAME={RABBITMQ_HOSTNAME}',
                    f'RABBITMQ_NODENAME={RABBITMQ_NODENAME}'],
                'volumes': [f'{SUBSTRA_FOLDER}/backup/rabbit-data:/var/lib/rabbitmq']
            },
            'flower': {
                'container_name': f'flower',
                'labels': ['substra'],
                'hostname': f'flower',
                'ports': ['5555:5555'],
                'image': 'substra/flower',
                'restart': 'unless-stopped',
                'command': 'celery flower -A substrabac',
                'logging': {'driver': 'json-file', 'options': {'max-size': '20m', 'max-file': '5'}},
                'environment': [f'CELERY_BROKER_URL={CELERY_BROKER_URL}',
                                'DJANGO_SETTINGS_MODULE=substrabac.settings.common'],
                'depends_on': ['rabbit', 'postgresql']
            }
        },
        'path': os.path.join(dir_path, './docker-compose-dynamic.yaml')}

    # generate nodes
    # TODO make sure nodes folder exists else warn

    for org in conf:
        org_name = org['name']
        org_name_stripped = org_name.replace('-', '')

        port = BACKEND_PORT[org_name_stripped]

        cpu_count = os.cpu_count()
        processes = 2 * int(cpu_count) + 1

        if launch_settings == 'prod':
            django_server = f'python3 manage.py collectstatic --noinput; '\
                            f'--module substrabac.wsgi --static-map /static=/usr/src/app/substrabac/statics ' \
                            f'--master --processes {processes} --threads 2 --need-app' \
                            f'--env DJANGO_SETTINGS_MODULE=substrabac.settings.server.prod uwsgi --http :{port} '
        else:
            django_server = f'DJANGO_SETTINGS_MODULE=substrabac.settings.server.dev ' \
                            f'python3 manage.py runserver --noreload 0.0.0.0:{port}'

        backend_global_env = [
            f'ORG={org_name_stripped}',
            f'SUBSTRABAC_ORG={org_name}',
            f'SUBSTRABAC_DEFAULT_PORT={port}',
            'SUBSTRABAC_PEER_PORT=internal',

            f'LEDGER_CONFIG_FILE={SUBSTRA_FOLDER}/conf/{org_name}/substrabac/conf.json',

            'PYTHONUNBUFFERED=1',
            'DATABASE_HOST=postgresql',

            f"TASK_CAPTURE_LOGS=True",
            f"TASK_CLEAN_EXECUTION_ENVIRONMENT=True",
            f"TASK_CACHE_DOCKER_IMAGES=False",

            f'CELERY_BROKER_URL={CELERY_BROKER_URL}',
            f'DJANGO_SETTINGS_MODULE=substrabac.settings.{launch_settings}',
        ]

        hlf_volumes = [
            # config (core.yaml + substrabac/conf.json)
            f'{SUBSTRA_FOLDER}/conf/{org_name}:{SUBSTRA_FOLDER}/conf/{org_name}:ro',

            # HLF files
            f'{org["core_peer_mspconfigpath"]}:{org["core_peer_mspconfigpath"]}:ro',
        ]

        # HLF files
        for tls_key in ['tlsCACerts', 'clientCert', 'clientKey']:
            hlf_volumes.append(f'{org["peer"][tls_key]}:{org["peer"][tls_key]}:ro')

        # load incoming/outgoing node fixtures/ that should not be executed in production env
        fixtures_command = ''
        user_command = ''
        if launch_settings == 'dev':
            fixtures_command = f"python manage.py init_nodes ./node/nodes/{org_name}MSP.json"
            user_command = f"python manage.py add_user foo barbar10"

        backend = {
            'container_name': f'substrabac.{org_name_stripped}.xyz',
            'labels': ['substra'],
            'image': 'substra/substrabac',
            'restart': 'unless-stopped',
            'ports': [f'{port}:{port}'],
            'command': f'/bin/bash -c "{wait_rabbit}; {wait_psql}; '
                       f'yes | python manage.py migrate; {fixtures_command}; {user_command}; {django_server}"',
            'logging': {'driver': 'json-file', 'options': {'max-size': '20m', 'max-file': '5'}},
            'environment': backend_global_env.copy(),
            'volumes': [
                f'{SUBSTRA_FOLDER}/medias:{SUBSTRA_FOLDER}/medias:rw',
                f'{SUBSTRA_FOLDER}/servermedias:{SUBSTRA_FOLDER}/servermedias:ro',
                f'{SUBSTRA_FOLDER}/static:/usr/src/app/substrabac/statics'] + hlf_volumes,
            'depends_on': ['postgresql', 'rabbit']}

        scheduler = {
            'container_name': f'{org_name_stripped}.scheduler',
            'labels': ['substra'],
            'hostname': f'{org_name}.scheduler',
            'image': 'substra/celeryworker',
            'restart': 'unless-stopped',
            'command': f'/bin/bash -c "{wait_rabbit}; {wait_psql}; '
                       f'celery -A substrabac worker -l info -n {org_name_stripped} '
                       f'-Q {org_name},scheduler,celery --hostname {org_name}.scheduler"',
            'logging': {'driver': 'json-file', 'options': {'max-size': '20m', 'max-file': '5'}},
            'environment': backend_global_env.copy(),
            'volumes': hlf_volumes,
            'depends_on': [f'substrabac{org_name_stripped}', 'postgresql', 'rabbit']}

        worker = {
            'container_name': f'{org_name_stripped}.worker',
            'labels': ['substra'],
            'hostname': f'{org_name}.worker',
            'image': 'substra/celeryworker',
            'restart': 'unless-stopped',
            'command': f'/bin/bash -c "{wait_rabbit}; {wait_psql}; '
                       f'celery -A substrabac worker -l info -n {org_name_stripped} '
                       f'-Q {org_name},{org_name}.worker,celery --hostname {org_name}.worker"',
            'logging': {'driver': 'json-file', 'options': {'max-size': '20m', 'max-file': '5'}},
            'environment': backend_global_env.copy(),
            'volumes': [
                '/var/run/docker.sock:/var/run/docker.sock',
                f'{SUBSTRA_FOLDER}/medias:{SUBSTRA_FOLDER}/medias:rw',
                f'{SUBSTRA_FOLDER}/servermedias:{SUBSTRA_FOLDER}/servermedias:ro'] + hlf_volumes,
            'depends_on': [f'substrabac{org_name_stripped}', 'rabbit']}

        # Check if we have nvidia docker
        if 'nvidia' in check_output(['docker', 'system', 'info', '-f', '"{{.Runtimes}}"']).decode('utf-8'):
            worker['runtime'] = 'nvidia'

        if launch_settings == 'dev':
            media_root = f'MEDIA_ROOT={SUBSTRA_FOLDER}/medias/{org_name_stripped}'
            worker['environment'].append(media_root)
            backend['environment'].append(media_root)
        else:
            default_domain = os.environ.get('SUBSTRABAC_DEFAULT_DOMAIN', '')
            if default_domain:
                backend['environment'].append(f"DEFAULT_DOMAIN={default_domain}")
                worker['environment'].append(f"DEFAULT_DOMAIN={default_domain}")
                scheduler['environment'].append(f"DEFAULT_DOMAIN={default_domain}")
            backend['environment'].append(f"RAVEN_URL={raven_backend_url}")
            scheduler['environment'].append(f"RAVEN_URL={raven_scheduler_url}")
            worker['environment'].append(f"RAVEN_URL={raven_worker_url}")

        docker_compose['substrabac_services']['substrabac' + org_name_stripped] = backend
        docker_compose['substrabac_services']['scheduler' + org_name_stripped] = scheduler
        docker_compose['substrabac_services']['worker' + org_name_stripped] = worker
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


def start(conf, launch_settings, no_backup):
    print('Generate docker-compose file\n')
    docker_compose = generate_docker_compose_file(conf, launch_settings)

    stop(docker_compose)

    if no_backup:
        print('Clean medias directory\n')
        call(['sh', os.path.join(dir_path, '../scripts/clean_media.sh')])
        print('Remove postgresql database\n')
        call(['rm', '-rf', f'{SUBSTRA_FOLDER}/backup/postgres-data'])
        print('Remove rabbit database\n')
        call(['rm', '-rf', f'{SUBSTRA_FOLDER}/backup/rabbit-data'])

    print('start docker-compose', flush=True)
    call(['docker-compose', '-f', docker_compose['path'], '--project-directory',
          os.path.join(dir_path, '../'), 'up', '-d', '--remove-orphans', '--build'])
    call(['docker', 'ps', '-a', '--format', 'table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}',
          '--filter', 'label=substra'])


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

    conf = [json.load(open(file_path, 'r')) for file_path in glob.glob(f'{SUBSTRA_FOLDER}/conf/*/substrabac/conf.json')]

    print('Build substrabac for : ', flush=True)
    print('  Organizations :', flush=True)
    for org in conf:
        print('   -', org['name'], flush=True)

    print('', flush=True)

    start(conf, launch_settings, no_backup)
