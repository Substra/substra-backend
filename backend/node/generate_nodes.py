import json
import os
import secrets


def generate_secret():
    return secrets.token_hex(64)


def generate(orgs):
    files = {}

    # TODO merge two loops
    # init file content
    for org in orgs:
        data = {
            'incoming_nodes': [],
            'outgoing_nodes': [],
        }
        files[org] = data

    for org in orgs:
        # create intern node (request from worker A to substrabac A)
        secret = generate_secret()
        files[org]['outgoing_nodes'].append({
            'node_id': org,
            'secret': secret
        })
        files[org]['incoming_nodes'].append({
            'node_id': org,
            'secret': secret
        })

        for other_org in filter(lambda x: x != org, orgs):
            # outgoing from server B to server A share same secret as incoming from server B in server A
            secret = generate_secret()
            files[other_org]['outgoing_nodes'].append({  # in server B
                'node_id': org,  # to server A
                'secret': secret
            })

            files[org]['incoming_nodes'].append({  # in server A
                'node_id': other_org,  # from server B
                'secret': secret
            })

    return files


def generate_for_orgs(orgs):
    files = generate(orgs)
    dir_path = os.path.dirname(os.path.realpath(__file__))
    nodes_path = os.path.join(dir_path, 'nodes')
    os.makedirs(nodes_path, exist_ok=True)
    for k, v in files.items():
        filepath = os.path.join(nodes_path, f'{k}.json')
        with open(filepath, 'w') as f:
            f.write(json.dumps(v, indent=4))


if __name__ == '__main__':
    orgs = ['owkinMSP', 'chu-nantesMSP', 'clbMSP']  # TODO should be discovered by discovery service

    generate_for_orgs(orgs)

