import hashlib
import os
import base64
import asyncio
import glob
import json
import tempfile

import OpenSSL
from Cryptodome.Util import asn1
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import NameOID
from hfc.fabric_ca.caservice import ca_service

from .org import ORG

from hfc.fabric import Client
from hfc.fabric.peer import Peer
from hfc.fabric.user import create_user
from hfc.fabric.orderer import Orderer
from hfc.util.keyvaluestore import FileKeyValueStore
from hfc.fabric.block_decoder import decode_fabric_MSP_config, decode_fabric_peers_info, decode_fabric_endpoints

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

LEDGER_SYNC_ENABLED = True

SUBSTRA_PATH = os.environ.get('SUBSTRA_PATH', '/substra')

LEDGER_CONFIG_FILE = os.environ.get('LEDGER_CONFIG_FILE', f'{SUBSTRA_PATH}/conf/{ORG}/substrabac/conf.json')


def deserialize_config(config_result):
    results = {'msps': {},
               'orderers': {}}

    for mspid in config_result.msps:
        results['msps'][mspid] = decode_fabric_MSP_config(
            config_result.msps[mspid].SerializeToString()
        )

    for mspid in config_result.orderers:
        results['orderers'][mspid] = decode_fabric_endpoints(
            config_result.orderers[mspid].endpoint
        )

    return results


def deserialize_members(members):
    peers = []

    for mspid in members.peers_by_org:
        peer = decode_fabric_peers_info(
            members.peers_by_org[mspid].peers
        )
        peers.append(peer)

    return peers


def deserialize_cc_query_res(cc_query_res):
    cc_queries = []

    for cc_query_content in cc_query_res.content:
        cc_query = {
            'chaincode': cc_query_content.chaincode,
            'endorsers_by_groups': {},
            'layouts': []
        }

        for group in cc_query_content.endorsers_by_groups:
            peers = decode_fabric_peers_info(
                cc_query_content.endorsers_by_groups[group].peers
            )

            cc_query['endorsers_by_groups'][group] = peers

        for layout_content in cc_query_content.layouts:
            layout = {
                'quantities_by_group': {
                    group: int(layout_content.quantities_by_group[group])
                    for group in layout_content.quantities_by_group
                }
            }
            cc_query['layouts'].append(layout)

        cc_queries.append(cc_query)

    return cc_queries


def deserialize_discovery(response):
    results = {
        'config': None,
        'members': [],
        'cc_query_res': None
    }

    for res in response.results:
        if res.config_result and res.config_result.msps and res.config_result.orderers:
            results['config'] = deserialize_config(res.config_result)

        if res.members:
            results['members'].extend(deserialize_members(res.members))

        if res.cc_query_res and res.cc_query_res.content:
            results['cc_query_res'] = deserialize_cc_query_res(res.cc_query_res)

    return results


def get_hfc_client():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client = Client()
    channel = client.new_channel(LEDGER['channel_name'])

    # Add peer from substrabac ledger config file
    peer = Peer(name=LEDGER['peer']['name'])
    peer.init_with_bundle({
        'url': f'{LEDGER["peer"]["host"]}:{PEER_PORT}',
        'grpcOptions': LEDGER['peer']['grpcOptions'],
        'tlsCACerts': {'path': LEDGER['peer']['tlsCACerts']},
        'clientKey': {'path': LEDGER['peer']['clientKey']},
        'clientCert': {'path': LEDGER['peer']['clientCert']},
    })
    client._peers[LEDGER['peer']['name']] = peer

    # Discover orderers and peers from channel discovery
    results = loop.run_until_complete(
        channel._discovery(
            LEDGER['requestor'],
            peer,
            config=True,
            local=False,
            interests=[{'chaincodes': [{'name': LEDGER['chaincode_name']}]}]
        )
    )

    results = deserialize_discovery(results)

    update_client_with_discovery(client, results)

    return loop, client


def get_hashed_modulus(cert):
    cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
    pub = cert.get_pubkey()
    pub_asn1 = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_ASN1, pub)
    pub_der = asn1.DerSequence()
    pub_der.decode(pub_asn1)

    modulus = pub_der[1]
    hashed_modulus = hashlib.sha256(str(modulus).encode()).hexdigest()

    return hashed_modulus


def write_pkey_key(path):
    pkey = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend())
    data = pkey.private_bytes(encoding=serialization.Encoding.PEM,
                              format=serialization.PrivateFormat.PKCS8,
                              encryption_algorithm=serialization.NoEncryption())
    with open(path, 'wb+') as f:
        f.write(data)
    return pkey


# SECURITY WARNING: keep the private key used in production secret!
# TODO will be override if docker is restarted, need to be passed as a volume
PKEY_FILE = os.path.normpath(os.path.join(PROJECT_ROOT, 'PKEY'))

# KEY CONFIGURATION
# Try to load the PKEY from our PKEY_FILE. If that fails, then generate
# a random PKEY and save it into our PKEY_FILE for future loading. If
# everything fails, then just raise an exception.
try:
    pkey = open(PKEY_FILE, 'rb').read().strip()
except IOError:
    try:
        pkey = write_pkey_key(PKEY_FILE)
    except IOError:
        raise Exception(f'Cannot open file `{PKEY_FILE}` for writing.')
else:
    pkey = serialization.load_pem_private_key(
        pkey,
        password=None,
        backend=default_backend()
    )

# END KEY CONFIGURATION


# TODO use dynamic data, and remove default
def get_csr(pkey,
            c_name,
            country_name='FR',
            st_name='Loire Atlantique',
            locality_name='Nantes',
            o_name='owkin',
            dns_name='rca-owkin'):
    csr = x509.CertificateSigningRequestBuilder().subject_name(x509.Name([
        # Provide various details about who we are.
        x509.NameAttribute(NameOID.COUNTRY_NAME, country_name),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, st_name),
        x509.NameAttribute(NameOID.LOCALITY_NAME, locality_name),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, o_name),
        x509.NameAttribute(NameOID.COMMON_NAME, c_name),
    ])).add_extension(
        # Describe what sites we want this certificate for.
        x509.SubjectAlternativeName([
            # Describe what sites we want this certificate for.
            x509.DNSName(dns_name),
        ]),
        critical=False,
        # Sign the CSR with our private key.
    ).sign(pkey, hashes.SHA256(), default_backend())

    return csr


def get_hfc_ca_client():
    port = LEDGER['ca']['port'][os.environ.get('SUBSTRABAC_CA_PORT', 'external')]
    target = f"https://{LEDGER['ca']['host']}:{port}"
    cacli = ca_service(target=target,
                       ca_certs_path=LEDGER['ca']['certfile'][os.environ.get('SUBSTRABAC_CA_CERT', 'external')],
                       ca_name=LEDGER['ca']['name'])

    return cacli


def update_client_with_discovery(client, discovery_results):

        # Get all msp tls root cert files
        tls_root_certs = {}
        for mspid, msp_info in discovery_results['config']['msps'].items():
            tls_root_certs[mspid] = base64.decodebytes(
                msp_info['tls_root_certs'].pop().encode()
            )

        # Load one peer per msp for endorsing transaction
        for msp in discovery_results['members']:
            peer_info = msp[0]
            if peer_info['mspid'] != LEDGER['client']['msp_id']:
                peer = Peer(name=peer_info['mspid'])

                with tempfile.NamedTemporaryFile() as tls_root_cert:
                    tls_root_cert.write(tls_root_certs[peer_info['mspid']])
                    tls_root_cert.flush()

                    url = peer_info['endpoint']
                    external_port = os.environ.get('SUBSTRABAC_PEER_PORT_EXTERNAL', None)
                    # use case for external development
                    if external_port:
                        url = f"{peer_info['endpoint'].split(':')[0]}:{external_port}"
                    peer.init_with_bundle({
                        'url': url,
                        'grpcOptions': {
                            'grpc-max-send-message-length': 15,
                            'grpc.ssl_target_name_override': peer_info['endpoint'].split(':')[0]
                        },
                        'tlsCACerts': {'path': tls_root_cert.name},
                        'clientKey': {'path': LEDGER['peer']['clientKey']},  # use peer creds (mutual tls)
                        'clientCert': {'path': LEDGER['peer']['clientCert']},  # use peer creds (mutual tls)
                    })

                client._peers[peer_info['mspid']] = peer

        # Load one orderer for broadcasting transaction
        orderer_mspid, orderer_info = list(discovery_results['config']['orderers'].items())[0]

        orderer = Orderer(name=orderer_mspid)

        with tempfile.NamedTemporaryFile() as tls_root_cert:
            tls_root_cert.write(tls_root_certs[orderer_mspid])
            tls_root_cert.flush()

            # Need loop
            orderer.init_with_bundle({
                'url': f"{orderer_info[0]['host']}:{orderer_info[0]['port']}",
                'grpcOptions': {
                    'grpc-max-send-message-length': 15,
                    'grpc.ssl_target_name_override': orderer_info[0]['host']
                },
                'tlsCACerts': {'path': tls_root_cert.name},
                'clientKey': {'path': LEDGER['peer']['clientKey']},  # use peer creds (mutual tls)
                'clientCert': {'path': LEDGER['peer']['clientCert']},  # use peer creds (mutual tls)
            })

        client._orderers[orderer_mspid] = orderer


if not os.path.exists(LEDGER_CONFIG_FILE):
    print('Cannot load LEDGER_CONFIG_FILE')
else:
    LEDGER = json.load(open(LEDGER_CONFIG_FILE, 'r'))

    PEER_PORT = LEDGER['peer']['port'][os.environ.get('SUBSTRABAC_PEER_PORT', 'external')]

    LEDGER['requestor'] = create_user(
        name=LEDGER['client']['name'],
        org=LEDGER['client']['org'],
        state_store=FileKeyValueStore(LEDGER['client']['state_store']),
        msp_id=LEDGER['client']['msp_id'],
        key_path=glob.glob(LEDGER['client']['key_path'])[0],
        cert_path=LEDGER['client']['cert_path']
    )

    LEDGER['hfc'] = get_hfc_client
    LEDGER['hfc_ca'] = {
        'client': get_hfc_ca_client(),
        'pkey': pkey
    }
