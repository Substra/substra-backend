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

from substrabac.settings.common import PROJECT_ROOT
from django.conf import settings

LEDGER = getattr(settings, 'LEDGER', None)


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

    channel_name = LEDGER['channel_name']
    chaincode_name = LEDGER['chaincode_name']
    core_peer_mspconfigpath = LEDGER['core_peer_mspconfigpath']
    peer = LEDGER['peer']

    # update config path for using right core.yaml and override msp config path
    os.environ['FABRIC_CFG_PATH'] = os.environ.get('FABRIC_CFG_PATH_ENV', peer['docker_core_dir'])
    os.environ['CORE_PEER_MSPCONFIGPATH'] = os.environ.get('CORE_PEER_MSPCONFIGPATH_ENV', core_peer_mspconfigpath)
    os.environ['CORE_PEER_ADDRESS'] = os.environ.get('CORE_PEER_ADDRESS_ENV', f'{peer["host"]}:{peer["port"]}')

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

    channel_name = LEDGER['channel_name']
    chaincode_name = LEDGER['chaincode_name']
    core_peer_mspconfigpath = LEDGER['core_peer_mspconfigpath']
    peer = LEDGER['peer']
    orderer = LEDGER['orderer']
    orderer_ca_file = orderer['ca']
    peer_key_file = peer['clientKey']
    peer_cert_file = peer['clientCert']

    # update config path for using right core.yaml and override msp config path
    os.environ['FABRIC_CFG_PATH'] = os.environ.get('FABRIC_CFG_PATH_ENV', peer['docker_core_dir'])
    os.environ['CORE_PEER_MSPCONFIGPATH'] = os.environ.get('CORE_PEER_MSPCONFIGPATH_ENV', core_peer_mspconfigpath)
    os.environ['CORE_PEER_ADDRESS'] = os.environ.get('CORE_PEER_ADDRESS_ENV', f'{peer["host"]}:{peer["port"]}')

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
           '--keyfile', peer_key_file,
           '--certfile', peer_cert_file]

    if sync:
        cmd += ['--waitForEvent', '--waitForEventTimeout', '45s']

    output = subprocess.run(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    st = status.HTTP_201_CREATED
    data = output.stdout.decode('utf-8')

    if not data:
        msg = output.stderr.decode('utf-8')
        data = {'message': msg}

        if 'Error' in msg or 'ERRO' in msg:
            # https://github.com/hyperledger/fabric/blob/eca1b14b7e3453a5d32296af79cc7bad10c7673b/peer/chaincode/common.go
            if "timed out waiting for txid on all peers" in msg or "failed to receive txid on all peers" in msg:
                st = status.HTTP_408_REQUEST_TIMEOUT
            else:
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


def get_hash(file, key=None):
    if file is None:
        return ''
    else:
        if isinstance(file, (str, bytes, os.PathLike)):
            with open(file, 'rb') as f:
                data = f.read()
        else:
            openedfile = file.open()
            data = openedfile.read()

        return compute_hash(data, key)


def compute_hash(bytes, key=None):
    sha256_hash = hashlib.sha256()

    if isinstance(bytes, str):
        bytes = bytes.encode()

    if key is not None and isinstance(key, str):
        bytes += key.encode()

    sha256_hash.update(bytes)

    return sha256_hash.hexdigest()


def get_computed_hash(url, key=None):
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

        computedHash = compute_hash(r.content, key)

        return r.content, computedHash


def get_remote_file(object, key=None):
    content, computed_hash = get_computed_hash(object['storageAddress'], key)

    if computed_hash != object['hash']:
        msg = 'computed hash is not the same as the hosted file. Please investigate for default of synchronization, corruption, or hacked'
        raise Exception(msg)

    return content, computed_hash


def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def uncompress_path(archive_path, to_directory):
    if zipfile.is_zipfile(archive_path):
        zip_ref = zipfile.ZipFile(archive_path, 'r')
        zip_ref.extractall(to_directory)
        zip_ref.close()
    elif tarfile.is_tarfile(archive_path):
        tar = tarfile.open(archive_path, 'r:*')
        tar.extractall(to_directory)
        tar.close()
    else:
        raise Exception('Archive must be zip or tar.gz')


def uncompress_content(archive_content, to_directory):
    if zipfile.is_zipfile(io.BytesIO(archive_content)):
        zip_ref = zipfile.ZipFile(io.BytesIO(archive_content))
        zip_ref.extractall(to_directory)
        zip_ref.close()
    else:
        try:
            tar = tarfile.open(fileobj=io.BytesIO(archive_content))
            tar.extractall(to_directory)
            tar.close()
        except tarfile.TarError:
            raise Exception('Archive must be zip or tar.gz')
