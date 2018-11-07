import os
import json

from subprocess import call


dir_path = os.path.dirname(os.path.realpath(__file__))


def generate_docker_compose_file(conf):
    try:
        from ruamel import yaml
    except ImportError:
        import yaml

    # Docker compose config
    docker_compose = {'substrabac_services': {},
                      'substrabac_tools': {'postgresql': {'container_name': 'postgresql',
                                                          'image': 'substra/postgresql',
                                                          'environment': ['POSTGRES_USER=postgres',
                                                                          'USER=postgres',
                                                                          'POSTGRES_PASSWORD=postgrespwd',
                                                                          'POSTGRES_DB=substrabac'],
                                                          'volumes': ['/substra/postgres-data:/var/lib/postgresql/data'],
                                                          },
                                           'celerybeat': {'container_name': 'celerybeat',
                                                          'image': 'substra/celerybeat',
                                                          'command': '/bin/bash -c "while ! { nc -z rabbit 5672 2>&1; }; do sleep 1; done; celery -A substrabac beat -l info -b rabbit"',
                                                          'environment': ['PYTHONUNBUFFERED=1',
                                                                          'DJANGO_SETTINGS_MODULE=substrabac.settings.dev'],
                                                          'volumes': ['/substra:/substra'],
                                                          'depends_on': ['rabbit']
                                                          },
                                           'rabbit': {'container_name': 'rabbit',
                                                      'image': 'rabbitmq:3',
                                                      'environment': ['RABBITMQ_DEFAULT_USER=guest',
                                                                      'RABBITMQ_DEFAULT_PASS=guest',
                                                                      'HOSTNAME=rabbitmq',
                                                                      'RABBITMQ_NODENAME=rabbitmq']},
                                           },
                      'path': os.path.join(dir_path, './docker-compose-dynamic.yaml')}

    for org_name, org_conf in conf['orgs'].items():
        org_name = org_name.replace('-', '')

        port = 8000
        if org_name == 'chunantes':
            port = 8001

        backend = {'container_name': '%s.substrabac' % org_name,
                   'image': 'substra/substrabac',
                   'ports': ['%s:%s' % (port, port)],
                   'command': '/bin/bash -c "while ! { nc -z postgresql 5432 2>&1; }; do sleep 1; done; python manage.py migrate --settings=substrabac.settings.dev.%s; python3 manage.py runserver 0.0.0.0:%s"' % (org_name, port),
                   'environment': ['DATABASE_HOST=postgresql',
                                   'DJANGO_SETTINGS_MODULE=substrabac.settings.dev.%s' % org_name,
                                   'PYTHONUNBUFFERED=1',
                                   'FABRIC_CFG_PATH=/substra/conf/%s/peer1/' % org_conf['name']],
                   'volumes': ['/substra:/substra',
                               '/substra/data/orgs/%s/user/msp:/opt/gopath/src/github.com/hyperledger/fabric/peer/msp' % org_conf['name']],
                   'depends_on': ['postgresql', 'rabbit']}

        worker = {'container_name': '%s.worker' % org_name,
                  'image': 'substra/celeryworker',
                  # 'runtime': 'nvidia',
                  'command': '/bin/bash -c "while ! { nc -z rabbit 5672 2>&1; }; do sleep 1; done; celery -A substrabac worker -l info -n %s -Q %s,celery -b rabbit"' % (org_name, org_conf['name']),
                  'environment': ['ORG=%s' % org_conf['name'],
                                  'DJANGO_SETTINGS_MODULE=substrabac.settings.dev.%s' % org_name,
                                  'PYTHONUNBUFFERED=1',
                                  'DATABASE_HOST=postgresql',
                                  'FABRIC_CFG_PATH=/substra/conf/%s/peer1/' % org_conf['name']],
                  'volumes': ['/substra:/substra',
                              '/var/run/docker.sock:/var/run/docker.sock',
                              '/substra/data/orgs/%s/user/msp:/opt/gopath/src/github.com/hyperledger/fabric/peer/msp' % org_conf['name']],
                  'depends_on': ['substrabac%s' % org_name, 'rabbit']}

        docker_compose['substrabac_services']['substrabac' + org_name] = backend
        docker_compose['substrabac_services']['worker' + org_name] = worker
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


def start(conf):

    print('Generate docker-compose file\n')
    docker_compose = generate_docker_compose_file(conf)

    stop(docker_compose)

    print('Clean medias directory\n')
    call(['sh', os.path.join(dir_path, '../substrabac/scripts/clean_media.sh')])

    print('start docker-compose', flush=True)
    call(['docker-compose', '-f', docker_compose['path'], '--project-directory',
          os.path.join(dir_path, '../'), 'up', '-d', '--remove-orphans'])
    call(['docker', 'ps', '-a'])


if __name__ == "__main__":

    call(['rm', '-rf', '/substra/postgres-data'])
    conf = json.load(open('/substra/conf/conf.json', 'r'))

    print('Build substrabac for : ', flush=True)
    print('  Organizations :', flush=True)
    for org_name in conf['orgs'].keys():
        print('   -', org_name, flush=True)

    print('', flush=True)

    start(conf)
