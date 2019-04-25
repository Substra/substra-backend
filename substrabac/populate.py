import argparse
import os
import json
import shutil
import time

import substra_sdk_py as substra

from termcolor import colored

dir_path = os.path.dirname(os.path.realpath(__file__))
server_path = '/substra/servermedias'

client = substra.Client()


def setup_config():
    print('Init config in /tmp/.substrabac for owkin and chunantes')
    client.create_config('owkin', 'http://owkin.substrabac:8000', '0.0')
    client.create_config('chunantes', 'http://chunantes.substrabac:8001', '0.0')


def create_or_get(data, profile, asset, dryrun=False, many=False,
                  register=False):

    client.set_config(profile)

    method = client.add if not register else client.register

    if dryrun:
        print('dryrun')
        try:
            r = method(asset, data, dryrun=True)
        except substra.exceptions.AssetAlreadyExist as e:
            r = e.response.json()
            print(colored(json.dumps(r, indent=2), 'cyan'))
        else:
            print(colored(json.dumps(r, indent=2), 'magenta'))

    print('real')
    try:
        r = method(asset, data)

    except substra.exceptions.AssetAlreadyExist as e:
        r = e.response.json()
        print(colored(json.dumps(r, indent=2), 'cyan'))
        key_or_keys = e.pkhash

    else:
        print(colored(json.dumps(r, indent=2), 'green'))
        key_or_keys = [x['pkhash'] for x in r] if many else r['pkhash']

    return key_or_keys


def update_datamanager(data_manager_key, data, profile):
    client.set_config(profile)
    r = client.update('data_manager', data_manager_key, data)
    print(colored(json.dumps(r, indent=2), 'green'))
    return r['pkhash']


def do_populate():
    setup_config()

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--one-org', action='store_true', default=False,
                        help='Launch populate with one org only')
    args = vars(parser.parse_args())

    org_0 = 'owkin'
    org_1 = org_0 if args['one_org'] else 'chunantes'

    print(f'will create datamanager with {org_1}')
    # create datamanager with org1
    data = {
        'name': 'ISIC 2018',
        'data_opener': os.path.join(dir_path, './fixtures/chunantes/datamanagers/datamanager0/opener.py'),
        'type': 'Images',
        'description': os.path.join(dir_path, './fixtures/chunantes/datamanagers/datamanager0/description.md'),
        'permissions': 'all',
    }
    data_manager_org1_key = create_or_get(data, org_1, 'data_manager', dryrun=True)

    ####################################################

    train_data_sample_keys = []
    print(f'register train data (from server) on datamanager {org_1} (will take datamanager creator as worker)')
    data_samples_path = ['./fixtures/chunantes/datasamples/train/0024306',
                         './fixtures/chunantes/datasamples/train/0024307']
    for d in data_samples_path:
        try:
            shutil.copytree(os.path.join(dir_path, d),
                            os.path.join(server_path, d))
        except FileExistsError:
            pass
    data = {
        'paths': [os.path.join(server_path, d) for d in data_samples_path],
        'data_manager_keys': [data_manager_org1_key],
        'test_only': False,
    }
    train_data_sample_keys = create_or_get(data, org_1, 'data_sample', dryrun=True, many=True, register=True)

    ####################################################

    print(f'create datamanager, test data and objective on {org_0}')
    data = {
        'name': 'Simplified ISIC 2018',
        'data_opener': os.path.join(dir_path, './fixtures/owkin/datamanagers/datamanager0/opener.py'),
        'type': 'Images',
        'description': os.path.join(dir_path, './fixtures/owkin/datamanagers/datamanager0/description.md'),
        'permissions': 'all'
    }
    data_manager_org0_key = create_or_get(data, org_0, 'data_manager')

    ####################################################

    print('register test data')
    data = {
        'paths': [
            os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024900.zip'),
            os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024901.zip')
        ],
        'data_manager_keys': [data_manager_org0_key],
        'test_only': True,
    }
    test_data_sample_keys = create_or_get(data, org_0, 'data_sample', many=True)

    ####################################################

    print('register test data 2')
    data = {
        'paths': [
            os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024902.zip'),
            os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024903.zip')
        ],
        'data_manager_keys': [data_manager_org0_key],
        'test_only': True,
    }
    create_or_get(data, org_0, 'data_sample', many=True)

    ####################################################

    print('register test data 3')
    data = {
        'paths': [
            os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024904.zip'),
            os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024905.zip')
        ],
        'data_manager_keys': [data_manager_org0_key],
        'test_only': True,
    }
    create_or_get(data, org_0, 'data_sample', many=True)

    ####################################################

    print('register objective')
    data = {
        'name': 'Skin Lesion Classification Objective',
        'description': os.path.join(dir_path, './fixtures/chunantes/objectives/objective0/description.md'),
        'metrics_name': 'macro-average recall',
        'metrics': os.path.join(dir_path, './fixtures/chunantes/objectives/objective0/metrics.py'),
        'permissions': 'all',
        'test_data_sample_keys': test_data_sample_keys,
        'test_data_manager_key': data_manager_org0_key
    }

    objective_key = create_or_get(data, org_0, 'objective', dryrun=True)

    ####################################################

    print('register objective without data manager and data sample')
    data = {
        'name': 'Skin Lesion Classification Objective',
        'description': os.path.join(dir_path, './fixtures/owkin/objectives/objective0/description.md'),
        'metrics_name': 'macro-average recall',
        'metrics': os.path.join(dir_path, './fixtures/owkin/objectives/objective0/metrics.py'),
        'permissions': 'all'
    }

    create_or_get(data, org_0, 'objective', dryrun=True)

    ####################################################

    # update datamanager
    print('update datamanager')
    data = {
        'objective_key': objective_key
    }
    update_datamanager(data_manager_org1_key, data, org_0)

    ####################################################

    # register algo
    print('register algo')
    data = {
        'name': 'Logistic regression',
        'file': os.path.join(dir_path, './fixtures/chunantes/algos/algo3/algo.tar.gz'),
        'description': os.path.join(dir_path, './fixtures/chunantes/algos/algo3/description.md'),
        'permissions': 'all',
    }
    algo_key = create_or_get(data, org_1, 'algo')

    ####################################################

    print('register algo 2')
    data = {
        'name': 'Neural Network',
        'file': os.path.join(dir_path, './fixtures/chunantes/algos/algo0/algo.tar.gz'),
        'description': os.path.join(dir_path, './fixtures/chunantes/algos/algo0/description.md'),
        'permissions': 'all',
    }
    algo_key_2 = create_or_get(data, org_1, 'algo')

    ####################################################

    data = {
        'name': 'Random Forest',
        'file': os.path.join(dir_path, './fixtures/chunantes/algos/algo4/algo.tar.gz'),
        'description': os.path.join(dir_path, './fixtures/chunantes/algos/algo4/description.md'),
        'permissions': 'all',
    }
    algo_key_3 = create_or_get(data, org_1, 'algo')

    ####################################################

    # create traintuple
    print('create traintuple')
    data = {
        'algo_key': algo_key,
        'objective_key': objective_key,
        'data_manager_key': data_manager_org1_key,
        'train_data_sample_keys': train_data_sample_keys,
        'tag': 'substra'
    }
    traintuple_key = create_or_get(data, org_1, 'traintuple')

    print('create second traintuple')
    data = {
        'algo_key': algo_key_2,
        'data_manager_key': data_manager_org1_key,
        'objective_key': objective_key,
        'train_data_sample_keys': train_data_sample_keys,
        'tag': 'My super tag'
    }

    create_or_get(data, org_1, 'traintuple')

    print('create third traintuple')
    data = {
        'algo_key': algo_key_3,
        'data_manager_key': data_manager_org1_key,
        'objective_key': objective_key,
        'train_data_sample_keys': train_data_sample_keys,
    }

    create_or_get(data, org_1, 'traintuple')

    ####################################################

    client.set_config(org_1)
    res = client.get('traintuple', traintuple_key)
    print(colored(json.dumps(res, indent=2), 'green'))

    # create testtuple
    print('create testtuple')
    data = {
        'traintuple_key': traintuple_key
    }

    testtuple_key = create_or_get(data, org_1, 'testtuple')

    if testtuple_key:
        client.set_config(org_1)
        res_t = client.get('testtuple', testtuple_key)
        print(colored(json.dumps(res_t, indent=2), 'yellow'))

        while res['status'] not in ('done', 'failed') or res_t['status'] not in ('done', 'failed'):
            print('-' * 100)
            try:
                client.set_config(org_1)
                res = client.get('traintuple', traintuple_key)
                print(colored(json.dumps(res, indent=2), 'green'))

                res_t = client.get('testtuple', testtuple_key)
                print(colored(json.dumps(res_t, indent=2), 'yellow'))
            except substra.exceptions.SDKException:
                print(colored('Error when getting subtuples', 'red'))
            time.sleep(3)

    else:
        while res['status'] not in ('done', 'failed'):
            print('-' * 100)
            try:
                client.set_config(org_1)
                res = client.get('traintuple', traintuple_key)
                print(colored(json.dumps(res, indent=2), 'green'))
            except substra.exceptions.SDKException:
                print(colored('Error when getting subtuple', 'red'))
            time.sleep(3)

        print('Testtuple create failed')


if __name__ == '__main__':
    try:
        do_populate()
    except substra.exceptions.HTTPError as e:
        try:
            error = e.response.json()
        except Exception:
            error_message = e.response.text
        else:
            error_message = json.dumps(error, indent=2)
        print(colored(str(e), 'red'))
        print(colored(error_message, 'red'))
