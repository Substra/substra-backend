#!/usr/bin/env python
import collections
import json
import os
import secrets
import yaml


def create_random_secret():
    return secrets.token_hex(64)


def generate_network_credentials(nodes):
    node_ids = [node_id for name, node_id in nodes]
    network_creds = collections.defaultdict(dict)

    # generate random outgoing credentials for all nodes
    for node_name, node_id in nodes:
        network_creds[node_id]['name'] = node_name
        network_creds[node_id]['outgoing'] = {
            other_id: create_random_secret()
            for other_id in node_ids if other_id != node_id
        }

    # parse outgoing credentials to set incoming credentials
    for node_id, node_creds in network_creds.items():
        node_creds['incoming'] = {
            other_id: network_creds[other_id]['outgoing'][node_id]
            for other_id in node_ids if other_id != node_id
        }

    return network_creds


def create_fixture(node_credentials):
    data = []
    for pk, v in node_credentials['outgoing'].items():
        data.append({
            'model': 'node.outgoingnode',
            'pk': pk,
            'fields': {'secret': v},
        })
    for pk, v in node_credentials['incoming'].items():
        data.append({
            'model': 'node.incomingnode',
            'pk': pk,
            'fields': {'secret': v},
        })
    return data


if __name__ == '__main__':
    node_ids = [
        ('chunantes', 'chu-nantesMSP'),
        ('owkin', 'owkinMSP'),
        ('clb', 'clbMSP'),
    ]
    # generate credentials
    network_credentials = generate_network_credentials(node_ids)
    print(json.dumps(network_credentials, sort_keys=True, indent=4))

    # create fixture files
    fixtures_path = 'substrabackend/node/fixtures'
    try:
        os.makedirs(fixtures_path)
    except OSError:
        pass
    for node_id, node_credentials in network_credentials.items():
        data = create_fixture(node_credentials)
        node_name = node_credentials['name']
        with open(os.path.join(fixtures_path, f'nodes-{node_name}.yaml'), 'w') as f:
            f.write(yaml.dump(data))
