conf = {
    'orgs': {
        'owkin': {
            'org_msp_dir': '/data/orgs/owkin/msp',
            'org_msp_id': 'owkinMSP',
            'admin_home': '/data/orgs/owkin/admin',
            'user_home': '/data/orgs/owkin/user',
            'anchor_tx_file': '/data/orgs/owkin/anchors.tx',
            'tls': {
                # careful, `ca-cert.pem` is the default cert name file and a example file with this name is already present in the docker image, do not forget to remove these examples files in your docker CMD overriding if naming the same way
                'certfile': '/data/orgs/owkin/ca-cert.pem',
                'clientkey': ''
            },
            'ca': {
                'name': 'rca-owkin',
                'host': 'rca-owkin',
                'certfile': 'ca-cert.pem',
                'port': 7054,
                'url': 'https://rca-owkin:7054',
                'logfile': 'data/logs/rca-owkin.log'
            },
            'users': {
                'bootstrap_admin': {
                    'name': 'admin',
                    'pass': 'adminpw'
                },
                'admin': {
                    'name': 'admin-owkin',
                    'pass': 'admin-owkinpw'
                },
                'user': {
                    'name': 'user-owkin',
                    'pass': 'user-owkinpw'
                },
            },
            'csr': {
                'cn': 'rca-owkin',
                'hosts': ['rca-orderer', 'rca-owkin', 'rca-chu-nantes']
            },
            'core': {
                'peer_home': '/opt/gopath/src/github.com/hyperledger/fabric/peer',
                'msp_config_path': '/opt/gopath/src/github.com/hyperledger/fabric/peer/msp',
                'tls': {
                    'key': 'server.key',
                    'cert': 'server.crt'
                }
            },
            'peers': [
                {
                    'name': 'peer1',
                    'pass': 'peer1pw',
                    'host': 'peer1-owkin',
                    'port': 7051
                },
                {
                    'name': 'peer2',
                    'pass': 'peer2pw',
                    'host': 'peer2-owkin',
                    'port': 7051
                }
            ]
        },
        'chu-nantes': {
            'org_msp_dir': '/data/orgs/chu-nantes/msp',
            'org_msp_id': 'chu-nantesMSP',
            'admin_home': '/data/orgs/chu-nantes/admin',
            'user_home': '/etc/hyperledger/fabric/orgs/chu-nantes/user',
            'anchor_tx_file': '/data/orgs/chu-nantes/anchors.tx',
            'tls': {
                # careful, `ca-cert.pem` is the default cert name file and a example file with this name is already present in the docker image, do not forget to remove these examples files if naming the same way
                'certfile': '/data/orgs/chu-nantes/ca-cert.pem',
                'clientkey': ''
            },
            'ca': {
                'name': 'rca-chu-nantes',
                'host': 'rca-chu-nantes',
                'certfile': 'ca-cert.pem',
                'port': 7054,
                'url': 'https://rca-chu-nantes:7054',
                'logfile': 'data/logs/rca-chu-nantes.log'
            },
            'users': {
                'bootstrap_admin': {
                    'name': 'admin',
                    'pass': 'adminpw'
                },
                'admin': {
                    'name': 'admin-chu-nantes',
                    'pass': 'admin-chu-nantespw'
                },
                'user': {
                    'name': 'user-chu-nantes',
                    'pass': 'user-chu-nantespw'
                },
            },
            'csr': {
                'cn': 'rca-chu-nantes',
                'hosts': ['rca-orderer', 'rca-owkin', 'rca-chu-nantes']
            },
            'core': {
                'peer_home': '/opt/gopath/src/github.com/hyperledger/fabric/peer',
                'msp_config_path': '/opt/gopath/src/github.com/hyperledger/fabric/peer/msp',
                'tls': {
                    'key': 'server.key',
                    'cert': 'server.crt'
                }
            },
            'peers': [
                {
                    'name': 'peer1',
                    'pass': 'peer1pw',
                    'host': 'peer1-chu-nantes',
                    'port': 7051
                },
                {
                    'name': 'peer2',
                    'pass': 'peer2pw',
                    'host': 'peer2-chu-nantes',
                    'port': 7051
                }
            ]
        },
    },
    'orderers': {
        'orderer': {
            'host': 'orderer1-orderer',
            'port': 7050,
            'tls': {
                # careful, `ca-cert.pem` is the default cert name file and a example file with this name is already present in the docker image, do not forget to remove these examples files in your docker CMD overriding if naming the same way
                'certfile': '/data/orgs/orderer/ca-cert.pem',
                'key': 'server.key',
                'cert': 'server.crt',
            },
            'ca': {
                'name': 'rca-orderer',
                'host': 'rca-orderer',
                'certfile': 'ca-cert.pem',
                'port': 7054,
                'url': 'https://rca-orderer:7054',
                'logfile': 'data/logs/rca-orderer.log',
            },
            'users': {
                'bootstrap_admin': {
                    'name': 'admin',
                    'pass': 'adminpw'
                },
                'admin': {
                    'name': 'admin-orderer',
                    'pass': 'admin-ordererpw'
                },
                'orderer': {
                    'name': 'orderer',
                    'pass': 'ordererpw'
                }
            },
            'csr': {
                'cn': 'rca-orderer',
                'hosts': ['rca-orderer', 'rca-owkin', 'rca-chu-nantes']
            },
            'org_msp_dir': '/data/orgs/orderer/msp',
            'org_msp_id': 'ordererMSP',
            'admin_home': '/data/orgs/orderer/admin',
            'broadcast_dir': '/data/logs/broadcast',
            'home': '/etc/hyperledger/orderer',
            'local_msp_dir': '/etc/hyperledger/orderer/msp',
        }
    },
    'misc': {
        'genesis_bloc_file': '/data/genesis.block',
        'channel_tx_file': '/data/channel.tx',
        'channel_name': 'mychannel',
        'chaincode_name': 'mycc',
        'config_block_file': '/tmp/config_block.pb',
        'config_update_envelope_file': '/tmp/config_update_as_envelope.pb',
        'setup_logfile': '/data/logs/setup.log',
        'setup_success_file': '/data/logs/setup.successful',
        'run_sumfile': '/data/logs/run.sum',
        'run_success_file': '/data/logs/run.successful',
        'run_fail_file': '/data/logs/run.fail'

    }
}
