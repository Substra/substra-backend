import io
import hashlib
import json
import os
import requests
import subprocess
import tarfile
from rest_framework import status

from django.conf import settings
from substrabac.settings.common import PROJECT_ROOT, LEDGER_CONF

#######
# /!\ #
#######

# careful, passing invoke parameters to queryLedger will NOT fail


def queryLedger(options):
    org = options['org']
    peer = options['peer']
    args = options['args']

    org_name = org['name']

    # update config path for using right core.yaml in /substra/conf/<org>/<peer>-host
    # careful, directory is <peer>-host not <peer>
    cfg_path = '/substra/conf/' + org_name + '/' + peer['name'] + '-host'
    os.environ['FABRIC_CFG_PATH'] = os.environ.get('FABRIC_CFG_PATH', cfg_path)

    channel_name = LEDGER_CONF['misc']['channel_name']
    chaincode_name = LEDGER_CONF['misc']['chaincode_name']

    print('Querying chaincode in the channel \'%(channel_name)s\' on the peer \'%(peer_host)s\' ...' % {
        'channel_name': channel_name,
        'peer_host': peer['host']
    }, flush=True)

    output = subprocess.run([os.path.join(PROJECT_ROOT, '../bin/peer'),
                             '--logging-level=debug',
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
            # TODO : Handle error
            pass

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

    return data, st


def invokeLedger(options, sync=False):
    org = options['org']
    peer = options['peer']
    args = options['args']

    org_name = org['name']

    orderer = LEDGER_CONF['orderers']['orderer']
    orderer_ca_file = '/substra/data/orgs/orderer/ca-cert.pem'
    orderer_key_file = '/substra/data/orgs/' + org_name + '/tls/' + peer['name'] + '/cli-client.key'
    orderer_cert_file = '/substra/data/orgs/' + org_name + '/tls/' + peer['name'] + '/cli-client.crt'

    # update config path for using right core.yaml in /substra/conf/<org>/<peer>-host
    # careful, directory is <peer>-host not <peer>
    cfg_path = '/substra/conf/' + org_name + '/' + peer['name'] + '-host'
    os.environ['FABRIC_CFG_PATH'] = os.environ.get('FABRIC_CFG_PATH', cfg_path)

    channel_name = LEDGER_CONF['misc']['channel_name']
    chaincode_name = LEDGER_CONF['misc']['chaincode_name']

    print('Sending invoke transaction to %(PEER_HOST)s ...' % {'PEER_HOST': peer['host']}, flush=True)

    cmd = [os.path.join(PROJECT_ROOT, '../bin/peer'),
           '--logging-level=debug',
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

    if sync:
        st = status.HTTP_200_OK
    else:
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
    content, computed_hash = get_computed_hash(object['storageAddress'])  # TODO pass cert

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
