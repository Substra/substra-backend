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


def create_data(data, profile, dryrun=False):
    client.set_config(profile)

    if dryrun:
        print('dry-run')
        res = client.add('data', data, dryrun=True)
        try:
            print(colored(json.dumps(res, indent=2), 'magenta'))
        except:
            print(colored(res.decode('utf-8'), 'red'))

    print('real')
    try:
        r = client.add('data', data)
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
                # wait until dataset is correctly created
                while not r['status_code'] == status.HTTP_200_OK:
                    r = client.get('data', pkhash)
                    print(colored(json.dumps(r, indent=2), 'blue'))
                    print('.', end='')
                    time.sleep(1)
                print(colored(json.dumps({'result': r['result']}, indent=2), 'green'))

        return data_keys


def update_dataset(dataset_key, data, profile):
    client.set_config(profile)

    r = client.update('dataset', dataset_key, data)

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
                r = client.get('dataset', dataset_key)
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

    print(f'will create dataset with {org_1}')
    # create dataset with org1
    data = {
        'name': 'ISIC 2018',
        'data_opener': os.path.join(dir_path, './fixtures/chunantes/datasets/59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd/opener.py'),
        'type': 'Images',
        'description': os.path.join(dir_path, './fixtures/chunantes/datasets/59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd/description.md'),
        'permissions': 'all',
    }
    dataset_org1_key = create_asset(data, org_1, 'dataset', dryrun=True)

    ####################################################

    train_data_keys = []
    if dataset_org1_key:
        print(f'register train data on dataset {org_1} (will take dataset creator as worker)')
        data = {
            'files': [
                os.path.join(dir_path, './fixtures/chunantes/data/train/0024306.zip'),
                os.path.join(dir_path, './fixtures/chunantes/data/train/0024307.zip')
            ],
            'dataset_keys': [dataset_org1_key],
            'test_only': False,
        }
        train_data_keys = create_data(data, org_1, True)

    ####################################################

    print(f'create dataset, test data and objective on {org_0}')
    data = {
        'name': 'Simplified ISIC 2018',
        'data_opener': os.path.join(dir_path, './fixtures/owkin/datasets/9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528/opener.py'),
        'type': 'Images',
        'description': os.path.join(dir_path, './fixtures/owkin/datasets/9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528/description.md'),
        'permissions': 'all'
    }
    dataset_org0_key = create_asset(data, org_0, 'dataset')

    ####################################################

    if dataset_org0_key and dataset_org1_key:
        print('register test data')
        data = {
            'files': [
                os.path.join(dir_path, './fixtures/owkin/data/test/0024900.zip'),
                os.path.join(dir_path, './fixtures/owkin/data/test/0024901.zip')
            ],
            'dataset_keys': [dataset_org0_key],
            'test_only': True,
        }
        test_data_keys = create_data(data, org_0, False)

        ####################################################

        print('register test data 2')
        data = {
            'files': [
                os.path.join(dir_path, './fixtures/owkin/data/test/0024902.zip'),
                os.path.join(dir_path, './fixtures/owkin/data/test/0024903.zip')
            ],
            'dataset_keys': [dataset_org0_key],
            'test_only': True,
        }
        test_data_keys_2 = create_data(data, org_0, False)

        ####################################################

        print('register test data 3')
        data = {
            'files': [
                os.path.join(dir_path, './fixtures/owkin/data/test/0024904.zip'),
                os.path.join(dir_path, './fixtures/owkin/data/test/0024905.zip')
            ],
            'dataset_keys': [dataset_org0_key],
            'test_only': True,
        }
        test_data_keys_3 = create_data(data, org_0, False)

        ####################################################

        print('register objective')
        data = {
            'name': 'Skin Lesion Classification Objective',
            'description': os.path.join(dir_path, './fixtures/chunantes/objectives/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/description.md'),
            'metrics_name': 'macro-average recall',
            'metrics': os.path.join(dir_path, './fixtures/chunantes/objectives/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/metrics.py'),
            'permissions': 'all',
            'test_data_keys': test_data_keys,
            'test_dataset_key': dataset_org0_key
        }

        objective_key = create_asset(data, org_0, 'objective', True)

        ####################################################

        # update dataset
        print('update dataset')
        data = {
            'objective_key': objective_key
        }
        update_dataset(dataset_org1_key, data, org_0)

        ####################################################

        if objective_key:
            # register algo
            print('register algo')
            data = {
                'name': 'Logistic regression',
                'file': os.path.join(dir_path, './fixtures/chunantes/algos/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/algo.tar.gz'),
                'description': os.path.join(dir_path, './fixtures/chunantes/algos/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/description.md'),
                'objective_key': objective_key,
                'permissions': 'all',
            }
            algo_key = create_asset(data, org_1, 'algo', True)

            ####################################################

            print('register algo 2')
            data = {
                'name': 'Neural Network',
                'file': os.path.join(dir_path, './fixtures/chunantes/algos/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/algo.tar.gz'),
                'description': os.path.join(dir_path, './fixtures/chunantes/algos/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/description.md'),
                'objective_key': objective_key,
                'permissions': 'all',
            }
            algo_key_2 = create_asset(data, org_1, 'algo', False)

            ####################################################

            data = {
                'name': 'Random Forest',
                'file': os.path.join(dir_path, './fixtures/chunantes/algos/f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284/algo.tar.gz'),
                'description': os.path.join(dir_path, './fixtures/chunantes/algos/f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284/description.md'),
                'objective_key': objective_key,
                'permissions': 'all',
            }
            algo_key_3 = create_asset(data, org_1, 'algo', False)

            ####################################################

            if algo_key and train_data_keys:
                # create traintuple
                print('create traintuple')
                data = {
                    'algo_key': algo_key,
                    'FLtask_key': '',
                    'in_models_keys': [],
                    'dataset_key': dataset_org1_key,
                    'train_data_keys': train_data_keys,
                }
                traintuple_key = create_traintuple(data, org_1)

                print('create second traintuple')
                data = {
                    'algo_key': algo_key_2,
                    'FLtask_key': '',
                    'in_models_keys': [],
                    'dataset_key': dataset_org1_key,
                    'train_data_keys': train_data_keys,
                }

                traintuple_key_2 = create_traintuple(data, org_1)

                print('create third traintuple')
                data = {
                    'algo_key': algo_key_3,
                    'FLtask_key': '',
                    'in_models_keys': [],
                    'dataset_key': dataset_org1_key,
                    'train_data_keys': train_data_keys,
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
