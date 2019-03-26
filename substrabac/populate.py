import argparse
import os
import json
import time
from substra_sdk_py import Client

from termcolor import colored

from rest_framework import status

dir_path = os.path.dirname(os.path.realpath(__file__))

client = Client()


# Use substra-sdk-py
def setup_config():
    print('Init config in /tmp/.substrabac for owkin and chunantes')

    client.create_config('owkin', 'http://owkin.substrabac:8000', '0.0')
    client.create_config('chunantes', 'http://chunantes.substrabac:8001', '0.0')


def create_asset(data, profile, asset, dryrun=False):
    client.set_config(profile)

    if dryrun:
        print('dry-run')

        res = client.add(asset, data, dryrun=True)
        try:
            print(colored(json.dumps(res, indent=2), 'magenta'))
        except:
            print(colored(res.decode('utf-8'), 'red'))

    print('real')
    try:
        r = client.add(asset, data)
    except Exception as e:
        print(colored(e, 'red'))
        return None
    else:
        print(colored(json.dumps({'result': r['result']}, indent=2), 'green'))

        if r['status_code'] == status.HTTP_400_BAD_REQUEST:
            if 'pkhash' not in r['result']:
                return None
        elif r['status_code'] == status.HTTP_408_REQUEST_TIMEOUT:
            print('timeout on ledger, will wait until available')
            pkhash = r['result']['pkhash']
            # wait until asset is correctly created
            while not r['status_code'] == status.HTTP_200_OK:
                r = client.get(asset, pkhash)
                print(json.dumps(r, indent=2))
                print('.', end='')
                time.sleep(1)
            print(colored(json.dumps({'result': r['result']}, indent=2), 'green'))

        return r['result']['pkhash']


def create_data_sample(data, profile, dryrun=False):
    client.set_config(profile)

    if dryrun:
        print('dry-run')
        res = client.add('data_sample', data, dryrun=True)
        try:
            print(colored(json.dumps(res, indent=2), 'magenta'))
        except:
            print(colored(res.decode('utf-8'), 'red'))

    print('real')
    try:
        r = client.add('data_sample', data)
    except Exception as e:
        print(colored(e, 'red'))
    else:
        print(colored(json.dumps({'result': r['result']}, indent=2), 'green'))

        if r['status_code'] == status.HTTP_400_BAD_REQUEST:
            if 'pkhash' not in r['result']:
                return None

        if r['status_code'] in (status.HTTP_408_REQUEST_TIMEOUT, status.HTTP_409_CONFLICT):
            data_keys = r['result']['pkhash']
        else:
            data_keys = [x['pkhash'] for x in r['result']]

        if r['status_code'] == status.HTTP_408_REQUEST_TIMEOUT:
            print('timeout on ledger, will wait until available')
            for pkhash in data_keys:
                # wait until datamanager is correctly created
                while not r['status_code'] == status.HTTP_200_OK:
                    r = client.get('data_sample', pkhash)
                    print(colored(json.dumps(r, indent=2), 'blue'))
                    print('.', end='')
                    time.sleep(1)
                print(colored(json.dumps({'result': r['result']}, indent=2), 'green'))

        return data_keys


def update_datamanager(data_manager_key, data, profile):
    client.set_config(profile)

    r = client.update('data_manager', data_manager_key, data)

    try:
        print(colored(json.dumps(r, indent=2), 'green'))
    except Exception as e:
        print(colored(e, 'red'))
    else:
        if r['status_code'] == status.HTTP_400_BAD_REQUEST:
            return None

        if r['status_code'] == status.HTTP_408_REQUEST_TIMEOUT:
            print('timeout on ledger, will wait until available')
            # wait until asset is correctly created
            while not r['status_code'] == status.HTTP_200_OK:
                r = client.get('data_manager', data_manager_key)
                print(colored(json.dumps(r, indent=2), 'blue'))
                print('.', end='')
                time.sleep(1)
            print(colored(json.dumps({'result': r['result']}, indent=2), 'green'))

        return r['result']['pkhash']


def create_traintuple(data, profile):
    client.set_config(profile)

    try:
        r = client.add('traintuple', data)
    except Exception as e:
        print(colored(e, 'red'))
    else:
        print(colored(json.dumps({'result': r['result']}, indent=2), 'green'))

        return r['result']['pkhash']


def create_testuple(data, profile):
    client.set_config(profile)
    try:
        r = client.add('testtuple', data)
    except Exception as e:
        print(colored(e, 'red'))
    else:
        print(colored(json.dumps({'result': r['result']}, indent=2), 'green'))

        # if r['status_code'] == status.HTTP_400_BAD_REQUEST:
        #     return r['pkhash']

        return r['result']['pkhash']


if __name__ == '__main__':
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
    data_manager_org1_key = create_asset(data, org_1, 'data_manager', dryrun=True)

    ####################################################

    train_data_sample_keys = []
    if data_manager_org1_key:
        print(f'register train data on datamanager {org_1} (will take datamanager creator as worker)')
        data = {
            'files': [
                os.path.join(dir_path, './fixtures/chunantes/datasamples/train/0024306.zip'),
                os.path.join(dir_path, './fixtures/chunantes/datasamples/train/0024307.zip')
            ],
            'data_manager_keys': [data_manager_org1_key],
            'test_only': False,
        }
        train_data_sample_keys = create_data_sample(data, org_1, True)

    ####################################################

    print(f'create datamanager, test data and objective on {org_0}')
    data = {
        'name': 'Simplified ISIC 2018',
        'data_opener': os.path.join(dir_path, './fixtures/owkin/datamanagers/datamanager0/opener.py'),
        'type': 'Images',
        'description': os.path.join(dir_path, './fixtures/owkin/datamanagers/datamanager0/description.md'),
        'permissions': 'all'
    }
    data_manager_org0_key = create_asset(data, org_0, 'data_manager')

    ####################################################

    if data_manager_org0_key and data_manager_org1_key:
        print('register test data')
        data = {
            'files': [
                os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024900.zip'),
                os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024901.zip')
            ],
            'data_manager_keys': [data_manager_org0_key],
            'test_only': True,
        }
        test_data_sample_keys = create_data_sample(data, org_0, False)

        ####################################################

        print('register test data 2')
        data = {
            'files': [
                os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024902.zip'),
                os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024903.zip')
            ],
            'data_manager_keys': [data_manager_org0_key],
            'test_only': True,
        }
        test_data_sample_keys_2 = create_data_sample(data, org_0, False)

        ####################################################

        print('register test data 3')
        data = {
            'files': [
                os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024904.zip'),
                os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024905.zip')
            ],
            'data_manager_keys': [data_manager_org0_key],
            'test_only': True,
        }
        test_data_sample_keys_3 = create_data_sample(data, org_0, False)

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

        objective_key = create_asset(data, org_0, 'objective', True)

        ####################################################

        # update datamanager
        print('update datamanager')
        data = {
            'objective_key': objective_key
        }
        update_datamanager(data_manager_org1_key, data, org_0)

        ####################################################

        if objective_key:
            # register algo
            print('register algo')
            data = {
                'name': 'Logistic regression',
                'file': os.path.join(dir_path, './fixtures/chunantes/algos/algo3/algo.tar.gz'),
                'description': os.path.join(dir_path, './fixtures/chunantes/algos/algo3/description.md'),
                'objective_key': objective_key,
                'permissions': 'all',
            }
            algo_key = create_asset(data, org_1, 'algo', True)

            ####################################################

            print('register algo 2')
            data = {
                'name': 'Neural Network',
                'file': os.path.join(dir_path, './fixtures/chunantes/algos/algo0/algo.tar.gz'),
                'description': os.path.join(dir_path, './fixtures/chunantes/algos/algo0/description.md'),
                'objective_key': objective_key,
                'permissions': 'all',
            }
            algo_key_2 = create_asset(data, org_1, 'algo', False)

            ####################################################

            data = {
                'name': 'Random Forest',
                'file': os.path.join(dir_path, './fixtures/chunantes/algos/algo4/algo.tar.gz'),
                'description': os.path.join(dir_path, './fixtures/chunantes/algos/algo4/description.md'),
                'objective_key': objective_key,
                'permissions': 'all',
            }
            algo_key_3 = create_asset(data, org_1, 'algo', False)

            ####################################################

            if algo_key and train_data_sample_keys:
                # create traintuple
                print('create traintuple')
                data = {
                    'algo_key': algo_key,
                    'FLtask_key': '',
                    'in_models_keys': [],
                    'data_manager_key': data_manager_org1_key,
                    'train_data_sample_keys': train_data_sample_keys,
                }
                traintuple_key = create_traintuple(data, org_1)

                print('create second traintuple')
                data = {
                    'algo_key': algo_key_2,
                    'FLtask_key': '',
                    'in_models_keys': [],
                    'data_manager_key': data_manager_org1_key,
                    'train_data_sample_keys': train_data_sample_keys,
                }

                traintuple_key_2 = create_traintuple(data, org_1)

                print('create third traintuple')
                data = {
                    'algo_key': algo_key_3,
                    'FLtask_key': '',
                    'in_models_keys': [],
                    'data_manager_key': data_manager_org1_key,
                    'train_data_sample_keys': train_data_sample_keys,
                }

                traintuple_key_3 = create_traintuple(data, org_1)

                ####################################################

                if traintuple_key:
                    client.set_config(org_1)
                    res = client.get('traintuple', traintuple_key)
                    print(colored(json.dumps(res, indent=2), 'green'))

                    # create testtuple
                    print('create testtuple')
                    data = {
                        'traintuple_key': traintuple_key
                    }

                    testtuple_key = create_testuple(data, org_1)
                    # testtuple_key = None

                    if testtuple_key:
                        client.set_config(org_1)
                        res_t = client.get('testtuple', testtuple_key)
                        print(colored(json.dumps(res_t, indent=2), 'yellow'))

                        while res['result']['status'] not in ('done', 'failed') or res_t['result']['status'] not in ('done', 'failed'):
                            print('-' * 100)
                            try:
                                client.set_config(org_1)
                                res = client.get('traintuple', traintuple_key)
                                print(colored(json.dumps(res, indent=2), 'green'))

                                res_t = client.get('testtuple', testtuple_key)
                                print(colored(json.dumps(res_t, indent=2), 'yellow'))
                            except:
                                print(colored('Error when getting subtuples', 'red'))
                            time.sleep(3)

                    else:
                        while res['result']['status'] not in ('done', 'failed'):
                            print('-' * 100)
                            try:
                                client.set_config(org_1)
                                res = client.get('traintuple', traintuple_key)
                                print(colored(json.dumps(res, indent=2), 'green'))
                            except:
                                print(colored('Error when getting subtuple', 'red'))
                            time.sleep(3)

                        print('Testtuple create failed')
