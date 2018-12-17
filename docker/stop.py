import os
from subprocess import call

dir_path = os.path.dirname(os.path.realpath(__file__))


def stop():
    print('stopping container')

    docker_compose_path = './docker-compose.yaml'

    if os.path.exists(os.path.join(dir_path, './docker-compose-dynamic.yaml')):
        docker_compose_path = './docker-compose-dynamic.yaml'

    call(['docker-compose', '-f', os.path.join(dir_path, docker_compose_path), '--project-directory',
          os.path.join(dir_path, '../'), 'down', '--remove-orphans'])

    # call(['rm', '-rf', '/substra/backup/postgres-data'])


if __name__ == "__main__":
    stop()
