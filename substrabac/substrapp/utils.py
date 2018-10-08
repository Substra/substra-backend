import hashlib
import json
import os
import subprocess

from rest_framework import status

from substrabac.settings.common import PROJECT_ROOT
from substrapp.conf import conf

#######
# /!\ #
#######

# careful, passing invoke parameters to queryLedger will NOT fail


def queryLedger(options):
    org = options['org']
    peer = options['peer']
    args = options['args']

    org_name = org['org_name']

    # update config path for using right core.yaml
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './conf/' + org_name + '/' + peer['name'])
    os.environ['FABRIC_CFG_PATH'] = cfg_path

    channel_name = conf['misc']['channel_name']
    chaincode_name = conf['misc']['chaincode_name']

    print('Querying chaincode in the channel \'%(channel_name)s\' on the peer \'%(peer_host)s\' ...' % {
        'channel_name': channel_name,
        'peer_host': peer['host']
    }, flush=True)

    output = subprocess.run([os.path.join(PROJECT_ROOT, '../bin/peer'),
                             '--logging-level=debug',
                             'chaincode', 'query',
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
            data = json.loads(data)
        except:
            pass
        else:
            if data is None:
                data = {}

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


def invokeLedger(options):
    org = options['org']
    peer = options['peer']
    args = options['args']

    org_name = org['org_name']

    # update config path for using right core.yaml
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), './conf/' + org_name + '/' + peer['name'])

    orderer = conf['orderers']['orderer']
    orderer_ca_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'conf/orderer/ca-cert.pem')
    orderer_key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'conf/' + org_name + '/tls/' + peer['name'] + '/cli-client.key')
    orderer_cert_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'conf/' + org_name + '/tls/' + peer['name'] + '/cli-client.crt')

    os.environ['FABRIC_CFG_PATH'] = cfg_path

    channel_name = conf['misc']['channel_name']
    chaincode_name = conf['misc']['chaincode_name']

    print('Sending invoke transaction to %(PEER_HOST)s ...' % {'PEER_HOST': peer['host']}, flush=True)

    output = subprocess.run([os.path.join(PROJECT_ROOT, '../bin/peer'),
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
                             '--certfile', orderer_cert_file
                             ],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    st = status.HTTP_201_CREATED
    data = output.stdout.decode('utf-8')
    if not data:
        msg = output.stderr.decode('utf-8')
        data = {'message': msg}

        if 'Error' in msg:
            st = status.HTTP_400_BAD_REQUEST
        elif 'access denied' in msg:
            st = status.HTTP_403_FORBIDDEN

    return data, st


def compute_hash(bytes):
    sha256_hash = hashlib.sha256()

    if isinstance(bytes, str):
        bytes = bytes.encode()

    sha256_hash.update(bytes)

    return sha256_hash.hexdigest()