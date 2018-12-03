import io
import hashlib
import json
import logging
import os
import requests
import subprocess
import tarfile
from rest_framework import status

from substrabac.settings.common import PROJECT_ROOT, LEDGER_CONF
from django.conf import settings


def clean_env_variables():
    del os.environ['FABRIC_CFG_PATH']
    del os.environ['CORE_PEER_MSPCONFIGPATH']
    del os.environ['CORE_PEER_ADDRESS']

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
    os.environ['FABRIC_CFG_PATH'] = os.environ.get('FABRIC_CFG_PATH', peer['docker_core_dir'])
    os.environ['CORE_PEER_MSPCONFIGPATH'] = os.environ.get('CORE_PEER_MSPCONFIGPATH', org['users']['user']['home'] + '/msp')
    os.environ['CORE_PEER_ADDRESS'] = os.environ.get('CORE_PEER_ADDRESS', '%s:%s' % (peer['host'], peer['host_port']))


    print('Querying chaincode in the channel \'%(channel_name)s\' on the peer \'%(peer_host)s\' ...' % {
        'channel_name': channel_name,
        'peer_host': peer['host']
    }, flush=True)

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

        msg = 'Query of channel \'%(channel_name)s\' on peer \'%(peer_host)s\' was successful\n' % {
            'channel_name': channel_name,
            'peer_host': peer['host']
        }
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
    os.environ['FABRIC_CFG_PATH'] = os.environ.get('FABRIC_CFG_PATH', peer['docker_core_dir'])
    os.environ['CORE_PEER_MSPCONFIGPATH'] = os.environ.get('CORE_PEER_MSPCONFIGPATH', org['users']['user']['home'] + '/msp')
    os.environ['CORE_PEER_ADDRESS'] = os.environ.get('CORE_PEER_ADDRESS', '%s:%s' % (peer['host'], peer['host_port']))

    print('Sending invoke transaction to %(PEER_HOST)s ...' % {'PEER_HOST': peer['host']}, flush=True)

    cmd = [os.path.join(PROJECT_ROOT, '../bin/peer'),
           '--logging-level', 'DEBUG',
           'chaincode', 'invoke',
           '-C', channel_name,
           '-n', chaincode_name,
           '-c', args,
           '-o', '%(host)s:%(port)s' % {'host': orderer['host'], 'port': orderer['port']},
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
    with open(file, 'rb') as f:
        data = f.read()
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
        raise Exception('Failed to check hash due to failed file fetching %s' % url)
    else:
        if r.status_code != 200:
            raise Exception(
                'Url: %(url)s to fetch file returned status code: %(st)s' % {'url': url, 'st': r.status_code})

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


def untar_algo(content, directory, traintuple):
    tar = tarfile.open(fileobj=io.BytesIO(content))
    tar.extractall(directory)
    tar.close()
