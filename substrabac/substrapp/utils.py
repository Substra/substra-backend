import io
import hashlib
import json
import glob
import logging
import os
import tempfile
from os.path import isfile, isdir

import requests
import tarfile
import zipfile

from checksumdir import dirhash
from rest_framework import status

from django.conf import settings

LEDGER = getattr(settings, 'LEDGER', None)

from hfc.fabric import Client
from hfc.fabric.peer import Peer
from hfc.fabric.user import create_user
from hfc.fabric.orderer import Orderer
from hfc.util.keyvaluestore import FileKeyValueStore


def clean_env_variables():
    os.environ.pop('FABRIC_CFG_PATH', None)
    os.environ.pop('CORE_PEER_MSPCONFIGPATH', None)
    os.environ.pop('CORE_PEER_ADDRESS', None)

#######
# /!\ #
#######

# careful, passing invoke parameters to queryLedger will NOT fail


def queryLedger(fcn, args=None):

    if args is None:
        args = []

    channel_name = LEDGER['channel_name']
    chaincode_name = LEDGER['chaincode_name']
    chaincode_version = LEDGER['chaincode_version']
    peer = LEDGER['peer']
    peer_port = peer["port"][os.environ.get('SUBSTRABAC_PEER_PORT', 'external')]
    requestor_config = LEDGER['client']

    client = Client()
    client.new_channel(channel_name)

    requestor = create_user(name=requestor_config['name'],
                            org=requestor_config['org'],
                            state_store=FileKeyValueStore(requestor_config['state_store']),
                            msp_id=requestor_config['msp_id'],
                            key_path=glob.glob(requestor_config['key_path'])[0],
                            cert_path=requestor_config['cert_path'])

    target_peer = Peer(name=peer['name'])
    target_peer.init_with_bundle({'url': f'{peer["host"]}:{peer_port}',
                                  'grpcOptions': peer['grpcOptions'],
                                  'tlsCACerts': {'path': peer['tlsCACerts']},
                                  'clientKey': {'path': peer['clientKey']},
                                  'clientCert': {'path': peer['clientCert']},
                                  })
    client._peers[peer['name']] = target_peer

    try:
        response = client.chaincode_query(
            requestor=requestor,
            channel_name=channel_name,
            peer_names=[peer['name']],
            args=args,
            cc_name=chaincode_name,
            cc_version=chaincode_version,
            fcn=fcn)
    except Exception as e:
        st = status.HTTP_400_BAD_REQUEST
        data = {'message': str(e)}
    else:
        msg = f'Query of channel \'{channel_name}\' on the peer \'{peer["host"]}\' was successful\n'
        print(msg, flush=True)

        st = status.HTTP_200_OK

        # TO DO : review parsing error in case of failure
        #         May have changed by using fabric-sdk-py
        try:
            data = json.loads(response)
        except:
            logging.error('Failed to json parse response in query')
            data = response

    finally:
        return data, st


def invokeLedger(fcn, args=None, sync=False):

    if args is None:
        args = []

    channel_name = LEDGER['channel_name']
    chaincode_name = LEDGER['chaincode_name']
    chaincode_version = LEDGER['chaincode_version']
    peer = LEDGER['peer']
    peer_port = peer["port"][os.environ.get('SUBSTRABAC_PEER_PORT', 'external')]

    orderer = LEDGER['orderer']

    requestor_config = LEDGER['client']

    client = Client()
    client.new_channel(channel_name)

    requestor = create_user(name=requestor_config['name'],
                            org=requestor_config['org'],
                            state_store=FileKeyValueStore(requestor_config['state_store']),
                            msp_id=requestor_config['msp_id'],
                            key_path=glob.glob(requestor_config['key_path'])[0],
                            cert_path=requestor_config['cert_path'])

    target_peer = Peer(name=peer['name'])
    target_peer.init_with_bundle({'url': f'{peer["host"]}:{peer_port}',
                                  'grpcOptions': peer['grpcOptions'],
                                  'tlsCACerts': {'path': peer['tlsCACerts']},
                                  'clientKey': {'path': peer['clientKey']},
                                  'clientCert': {'path': peer['clientCert']},
                                  })
    client._peers[peer['name']] = target_peer

    target_orderer = Orderer(name=orderer['name'])
    target_orderer.init_with_bundle({'url': f'{orderer["host"]}:{orderer["port"]}',
                                     'grpcOptions': orderer['grpcOptions'],
                                     'tlsCACerts': {'path': orderer['ca']},
                                     'clientKey': {'path': orderer['clientKey']},
                                     'clientCert': {'path': orderer['clientCert']},
                                     })
    client._orderers[orderer['name']] = target_orderer

    try:
        response = client.chaincode_invoke(
            requestor=requestor,
            channel_name=channel_name,
            peer_names=[peer['name']],
            args=args,
            cc_name=chaincode_name,
            cc_version=chaincode_version,
            fcn=fcn,
            wait_for_event=sync,
            wait_for_event_timeout=45)
    except TimeoutError as e:
        st = status.HTTP_408_REQUEST_TIMEOUT
        data = {'message': str(e)}
    except Exception as e:
        st = status.HTTP_400_BAD_REQUEST
        data = {'message': str(e)}
    else:
        # TO DO : review parsing error in case of failure
        #         May have changed by using fabric-sdk-py
        # elif 'access denied' in msg or 'authentication handshake failed' in msg:
        #     st = status.HTTP_403_FORBIDDEN

        st = status.HTTP_201_CREATED
        data = {'pkhash': response}

    finally:
        return data, st


def get_dir_hash(archive_content):
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            content = archive_content.read()
            archive_content.seek(0)
            uncompress_content(content, temp_dir)
        except Exception as e:
            logging.error(e)
            raise e
        else:
            return dirhash(temp_dir, 'sha256')


def get_hash(file, key=None):
    if file is None:
        return ''
    else:
        if isinstance(file, (str, bytes, os.PathLike)):
            if isfile(file):
                with open(file, 'rb') as f:
                    data = f.read()
            elif isdir(file):
                return dirhash(file, 'sha256')
            else:
                return ''
        else:
            openedfile = file.open()
            data = openedfile.read()
            openedfile.seek(0)

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
            raise Exception('Archive must be zip or tar.*')
