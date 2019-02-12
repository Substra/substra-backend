import json
import os

dir_path = '.'


def generate_network_file(conf):
    network_conf = {'name': 'substra',
                    'description': 'Substra network',
                    'version': '0.1',
                    'client': {'organization': 'owkin',
                               'credentialStore': {'path': '/tmp/hfc-kvs',
                                                   'cryptoStore': {
                                                       'path': '/tmp/hfc-cvs'},
                                                   'wallet': 'wallet-name'}
                               },
                    'organizations': {},
                    'orderers': {},
                    'peers': {},
                    'certificateAuthorities': {}

                    }
    for orderer in conf['orderers']:
        # print(orderer)
        admin_private_key = \
            os.listdir('%s/msp/keystore/' % orderer['admin_home'])[0]
        network_conf['organizations'][orderer['name']] = {
            'mspid': orderer['msp_id'],
            'orderers': [orderer['host']],
            'certificateAuthorities': [orderer['ca']['name']],
            'users': {'admin': {
                'cert': '%s/msp/signcerts/cert.pem' % orderer['admin_home'],
                'private_key': '%s/msp/keystore/%s' % (
                    orderer['admin_home'], admin_private_key)}
            }
        }
        network_conf['orderers'][orderer['name']] = {
            'url': '%s:%s' % (orderer['host'], orderer['port']),
            'grpcOptions': {'grpc.ssl_target_name_override': orderer['host'],
                            'grpc-max-send-message-length': 15
                            },
            'tlsCACerts': {'path': orderer['ca']['certfile']}
        }

        network_conf['certificateAuthorities'][orderer['ca']['name']] = {
            'url': '%s:%s' % (
                orderer['ca']['host'], orderer['ca']['host_port']),
            'grpcOptions': {'verify': True},
            'tlsCACerts': {'path': orderer['ca']['certfile']},
            'registrar': [{'enrollId': orderer['users']['admin']['name'],
                           'enrollSecret': orderer['users']['admin']['pass']
                           }]
        }

    for org in conf['orgs']:
        # print(org)
        admin_private_key = \
            os.listdir('%s/msp/keystore/' % org['users']['admin']['home'])[0]
        user_private_key = \
            os.listdir('%s/msp/keystore/' % org['users']['user']['home'])[0]
        network_conf['organizations'][org['name']] = {'mspid': org['msp_id'],
                                                      'peers': [peer['host']
                                                                for peer in
                                                                org['peers']],
                                                      'certificateAuthorities': [
                                                          org['ca']['name']],
                                                      'users': {'admin': {
                                                          'cert': '%s/msp/signcerts/cert.pem' %
                                                                  org['users'][
                                                                      'admin'][
                                                                      'home'],
                                                          'private_key': '%s/msp/keystore/%s' % (
                                                              org['users'][
                                                                  'admin'][
                                                                  'home'],
                                                              admin_private_key)},
                                                          'user': {
                                                              'cert': '%s/msp/signcerts/cert.pem' %
                                                                      org[
                                                                          'users'][
                                                                          'user'][
                                                                          'home'],
                                                              'private_key': '%s/msp/keystore/%s' % (
                                                                  org['users'][
                                                                      'user'][
                                                                      'home'],
                                                                  user_private_key)}
                                                      }
                                                      }

        network_conf['certificateAuthorities'][org['ca']['name']] = {
            'url': '%s:%s' % (org['ca']['host'], org['ca']['host_port']),
            'grpcOptions': {'verify': True},
            'tlsCACerts': {'path': org['ca']['certfile']},
            'registrar': [{'enrollId': org['users']['admin']['name'],
                           'enrollSecret': org['users']['admin']['pass']
                           }]
        }

        for peer in org['peers']:
            network_conf['peers'][peer['host']] = {
                'url': '%s:%s' % (peer['host'], peer['host_port']),
                'eventUrl': '%s:%s' % (peer['host'], peer['host_event_port']),
                'grpcOptions': {
                    'grpc.ssl_target_name_override': peer['host'],
                    'grpc.http2.keepalive_time': 15,
                },
                'tlsCACerts': {'path': peer['tls']['serverCa']}
            }

    with open(os.path.join(dir_path, 'network.json'), 'w') as outfile:
        json.dump(network_conf, outfile, indent=4, sort_keys=True)

    return network_conf


if __name__ == "__main__":
    conf_path = '/substra/conf/conf.json'
    conf = json.load(open(conf_path, 'r'))
    generate_network_file(conf)
