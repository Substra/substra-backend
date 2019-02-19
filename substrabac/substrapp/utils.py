import io
import hashlib
import json
import logging
import os
import requests
import subprocess
import tarfile
import zipfile
from rest_framework import status

from substrabac.settings.common import PROJECT_ROOT, LEDGER_CONF
from django.conf import settings


def clean_env_variables():
    os.environ.pop('FABRIC_CFG_PATH', None)
    os.environ.pop('CORE_PEER_MSPCONFIGPATH', None)
    os.environ.pop('CORE_PEER_ADDRESS', None)

#######
# /!\ #
#######

# careful, passing invoke parameters to queryLedger will NOT fail


def queryLedger(options):
    args = options['args']

    org = settings.LEDGER['org']
    peer = settings.LEDGER['peer']
    channel_name = LEDGER_CONF['misc']['channel_name']
    chaincode_name = LEDGER_CONF['misc']['chaincode_name']

    # update config path for using right core.yaml and override msp config path
    os.environ['FABRIC_CFG_PATH'] = os.environ.get('FABRIC_CFG_PATH_ENV', peer['docker_core_dir'])
    os.environ['CORE_PEER_MSPCONFIGPATH'] = os.environ.get('CORE_PEER_MSPCONFIGPATH_ENV', org['users']['user']['home'] + '/msp')
    os.environ['CORE_PEER_ADDRESS'] = os.environ.get('CORE_PEER_ADDRESS_ENV', f'{peer["host"]}:{peer["host_port"]}')

    print(f'Querying chaincode in the channel \'{channel_name}\' on the peer \'{peer["host"]}\' ...', flush=True)

    output = subprocess.run([os.path.join(PROJECT_ROOT, '../bin/peer'),
                             '--logging-level', 'DEBUG',
                             'chaincode', 'query',
                             '-x',
                             '-C', channel_name,
                             '-n', chaincode_name,
                             '-c', args],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    st = status.HTTP_200_OK
    data = output.stdout.decode('utf-8')
    if data:
        # json transformation if needed
        try:
            data = json.loads(bytes.fromhex(data.rstrip()).decode('utf-8'))
        except:
            logging.error('Failed to json parse hexadecimal response in query')

        msg = f'Query of channel \'{channel_name}\' on the peer \'{peer["host"]}\' was successful\n'
        print(msg, flush=True)
    else:
        try:
            msg = output.stderr.decode('utf-8').split('Error')[2].split('\n')[0]
            data = {'message': msg}
        except:
            msg = output.stderr.decode('utf-8')
            data = {'message': msg}
        finally:
            st = status.HTTP_400_BAD_REQUEST
            if 'access denied' in msg:
                st = status.HTTP_403_FORBIDDEN

    clean_env_variables()

    return data, st


def invokeLedger(options, sync=False):
    args = options['args']

    org = settings.LEDGER['org']
    peer = settings.LEDGER['peer']
    orderer = settings.LEDGER['orderer']
    channel_name = LEDGER_CONF['misc']['channel_name']
    chaincode_name = LEDGER_CONF['misc']['chaincode_name']
    orderer_ca_file = orderer['ca']['certfile']
    orderer_key_file = peer['tls']['clientKey']
    orderer_cert_file = peer['tls']['clientCert']

    # update config path for using right core.yaml and override msp config path
    os.environ['FABRIC_CFG_PATH'] = os.environ.get('FABRIC_CFG_PATH_ENV', peer['docker_core_dir'])
    os.environ['CORE_PEER_MSPCONFIGPATH'] = os.environ.get('CORE_PEER_MSPCONFIGPATH_ENV', org['users']['user']['home'] + '/msp')
    os.environ['CORE_PEER_ADDRESS'] = os.environ.get('CORE_PEER_ADDRESS_ENV', f'{peer["host"]}:{peer["host_port"]}')

    print(f'Sending invoke transaction to {peer["host"]} ...', flush=True)

    cmd = [os.path.join(PROJECT_ROOT, '../bin/peer'),
           '--logging-level', 'DEBUG',
           'chaincode', 'invoke',
           '-C', channel_name,
           '-n', chaincode_name,
           '-c', args,
           '-o', f'{orderer["host"]}:{orderer["port"]}',
           '--cafile', orderer_ca_file,
           '--tls',
           '--clientauth',
           '--keyfile', orderer_key_file,
           '--certfile', orderer_cert_file]

    if sync:
        cmd.append('--waitForEvent')

    output = subprocess.run(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    st = status.HTTP_201_CREATED
    data = output.stdout.decode('utf-8')

    if not data:
        msg = output.stderr.decode('utf-8')
        data = {'message': msg}

        if 'Error' in msg or 'ERRO' in msg:
            st = status.HTTP_400_BAD_REQUEST
        elif 'access denied' in msg or 'authentication handshake failed' in msg:
            st = status.HTTP_403_FORBIDDEN
        elif 'Chaincode invoke successful' in msg:
            st = status.HTTP_201_CREATED
            try:
                msg = msg.split('result: status:')[1].split('\n')[0].split('payload:')[1].strip().strip('"')
            except:
                pass
            finally:
                data = {'pkhash': msg}

    clean_env_variables()

    return data, st


def get_hash(file):
    if file is None:
        return ''
    else:
        if isinstance(file, (str, bytes, os.PathLike)):
            with open(file, 'rb') as f:
                data = f.read()
        else:
            openedfile = file.open()
            data = openedfile.read()

        return compute_hash(data)


def compute_hash(bytes):
    sha256_hash = hashlib.sha256()

    if isinstance(bytes, str):
        bytes = bytes.encode()

    sha256_hash.update(bytes)

    return sha256_hash.hexdigest()


def get_computed_hash(url):
    username = getattr(settings, 'BASICAUTH_USERNAME', None)
    password = getattr(settings, 'BASICAUTH_PASSWORD', None)

    kwargs = {}

    if username is not None and password is not None:
        kwargs.update({'auth': (username, password)})

    if settings.DEBUG:
        kwargs.update({'verify': False})

    try:
        r = requests.get(url, headers={'Accept': 'application/json;version=0.0'}, **kwargs)
    except:
        raise Exception(f'Failed to check hash due to failed file fetching {url}')
    else:
        if r.status_code != 200:
            raise Exception(
                f'Url: {url} to fetch file returned status code: {r.status_code}')

        computedHash = compute_hash(r.content)

        return r.content, computedHash


def get_remote_file(object):
    content, computed_hash = get_computed_hash(object['storageAddress'])

    if computed_hash != object['hash']:
        msg = 'computed hash is not the same as the hosted file. Please investigate for default of synchronization, corruption, or hacked'
        raise Exception(msg)

    return content, computed_hash


def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def uncompress_path(archive_path, to_directory):
    if archive_path[-4:] == '.zip':
        zip_ref = zipfile.ZipFile(archive_path, 'r')
        zip_ref.extractall(to_directory)
        zip_ref.close()
    elif archive_path[-7:] == '.tar.gz':
        tar = tarfile.open(archive_path, 'r:gz')
        tar.extractall(to_directory)
        tar.close()
    else:
        raise Exception('Archive must be zip or tar.gz')


def uncompress_content(archive_content, to_directory):
    try:
        zip_ref = zipfile.ZipFile(io.BytesIO(archive_content))
        zip_ref.extractall(to_directory)
        zip_ref.close()
    except:
        try:
            tar = tarfile.open(fileobj=io.BytesIO(archive_content))
            tar.extractall(to_directory)
            tar.close()
        except:
            print('failed')
            raise Exception('Archive must be zip or tar.gz')
