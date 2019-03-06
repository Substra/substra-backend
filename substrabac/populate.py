import argparse
import os
import json
import time
from subprocess import PIPE, Popen as popen
from substra_sdk_py import Client

from termcolor import colored

from rest_framework import status

dir_path = os.path.dirname(os.path.realpath(__file__))

client = Client()

# Use substra-sdk-py
def setup_config():
    print('Init config in /tmp/.substrabac for owkin and chunantes')

    client.create_config('owkin', 'http://owkin.substrabac:8000', '0.0')
    client.create_config('chunantes', 'http://owkin.substrabac:8001', '0.0')


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
                res = popen(['substra', 'get', asset, pkhash, f'--profile={profile}', '--config=/tmp/.substrabac'], stdout=PIPE).communicate()[0]
                r = json.loads(res.decode('utf-8'))
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
                    res = popen(['substra', 'get', 'data', pkhash, f'--profile={profile}', '--config=/tmp/.substrabac'], stdout=PIPE).communicate()[0]
                    r = json.loads(res.decode('utf-8'))
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
                res = popen(
                    ['substra', 'get', 'dataset', dataset_key, f'--profile={profile}',
                     '--config=/tmp/.substrabac'], stdout=PIPE).communicate()[0]
                r = json.loads(res.decode('utf-8'))
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
        'data_opener': os.path.join(dir_path, './fixtures/chunantes/datasets/6ed251c2d71d99b206bf11e085e69c315e1861630655b3ce6fd55ca9513ef181/opener.py'),
        'type': 'Images',
        'description': os.path.join(dir_path, './fixtures/chunantes/datasets/6ed251c2d71d99b206bf11e085e69c315e1861630655b3ce6fd55ca9513ef181/description.md'),
        'permissions': 'all',
    }
    dataset_org1_key = create_asset(data, org_1, 'dataset', dryrun=True)

    ####################################################

    train_data_keys = []
    if dataset_org1_key:
        print(f'register train data on dataset {org_1} (will take dataset creator as worker)')
        data = {
            'files': [
                os.path.join(dir_path, './fixtures/chunantes/data/62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a/0024700.zip'),
                os.path.join(dir_path, './fixtures/chunantes/data/42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9/0024899.zip')
            ],
            'dataset_keys': [dataset_org1_key],
            'test_only': False,
        }
        train_data_keys = create_data(data, org_1, True)

    ####################################################

    print(f'create dataset, test data and challenge on {org_0}')
    data = {
        'name': 'Simplified ISIC 2018',
        'data_opener': os.path.join(dir_path, './fixtures/owkin/datasets/bcfdad31dbe9163e9f254a2b9a485f2dd5d035ecce4a1331788039f2bccdf7af/opener.py'),
        'type': 'Images',
        'description': os.path.join(dir_path, './fixtures/owkin/datasets/bcfdad31dbe9163e9f254a2b9a485f2dd5d035ecce4a1331788039f2bccdf7af/description.md'),
        'permissions': 'all'
    }
    dataset_org0_key = create_asset(data, org_0, 'dataset')

    ####################################################

    if dataset_org0_key and dataset_org1_key:
        print('register test data')
        data = {
            'files': [
                os.path.join(dir_path, './fixtures/owkin/data/e11aeec290749e4c50c91305e10463eced8dbf3808971ec0c6ea0e36cb7ab3e1/0024900.zip'),
                os.path.join(dir_path, './fixtures/owkin/data/4b5152871b181d10ee774c10458c064c70710f4ba35938f10c0b7aa51f7dc010/0024701.zip')
            ],
            'dataset_keys': [dataset_org0_key],
            'test_only': True,
        }
        test_data_keys = create_data(data, org_0, False)

        ####################################################

        print('register test data 2')
        data = {
            'files': [
                os.path.join(dir_path, './fixtures/owkin/data/93e4b1e040b08cfa8a68b13f9dddb95a6672e8a377378545b2b1254691cfc060/0024317.zip'),
                os.path.join(dir_path, './fixtures/owkin/data/eed4c6ea09babe7ca6428377fff6e54102ef5cdb0cae593732ddbe3f224217cb/0024316.zip')
            ],
            'dataset_keys': [dataset_org0_key],
            'test_only': True,
        }
        test_data_keys_2 = create_data(data, org_0, False)

        ####################################################

        print('register test data 3')
        data = {
            'files': [
                os.path.join(dir_path, './fixtures/owkin/data/2d0f943aa81a9cb3fe84b162559ce6aff068ccb04e0cb284733b8f9d7e06517e/0024315.zip'),
                os.path.join(dir_path, './fixtures/owkin/data/533ee6e7b9d8b247e7e853b24547f57e6ef351852bac0418f13a0666173448f1/0024318.zip')
            ],
            'dataset_keys': [dataset_org0_key],
            'test_only': True,
        }
        test_data_keys_3 = create_data(data, org_0, False)

        ####################################################

        print('register challenge')
        data = {
            'name': 'Skin Lesion Classification Challenge',
            'description': os.path.join(dir_path, './fixtures/chunantes/challenges/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/description.md'),
            'metrics_name': 'macro-average recall',
            'metrics': os.path.join(dir_path, './fixtures/chunantes/challenges/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/metrics.py'),
            'permissions': 'all',
            'test_data_keys': test_data_keys,
            'test_dataset_key': dataset_org0_key
        }

        challenge_key = create_asset(data, org_0, 'challenge', True)

        ####################################################

        # update dataset
        print('update dataset')
        data = {
            'challenge_key': challenge_key
        }
        update_dataset(dataset_org1_key, data, org_0)

        ####################################################

        if challenge_key:
            # register algo
            print('register algo')
            data = {
                'name': 'Logistic regression',
                'file': os.path.join(dir_path, './fixtures/chunantes/algos/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/algo.tar.gz'),
                'description': os.path.join(dir_path, './fixtures/chunantes/algos/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/description.md'),
                'challenge_key': challenge_key,
                'permissions': 'all',
            }
            algo_key = create_asset(data, org_1, 'algo', True)

            ####################################################

            print('register algo 2')
            data = {
                'name': 'Neural Network',
                'file': os.path.join(dir_path, './fixtures/chunantes/algos/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/algo.tar.gz'),
                'description': os.path.join(dir_path, './fixtures/chunantes/algos/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/description.md'),
                'challenge_key': challenge_key,
                'permissions': 'all',
            }
            algo_key_2 = create_asset(data, org_1, 'algo', False)

            ####################################################

            data = {
                'name': 'Random Forest',
                'file': os.path.join(dir_path, './fixtures/chunantes/algos/f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284/algo.tar.gz'),
                'description': os.path.join(dir_path, './fixtures/chunantes/algos/f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284/description.md'),
                'challenge_key': challenge_key,
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
                    'input_models_keys': [],
                    'dataset_key': dataset_org1_key,
                    'train_data_keys': train_data_keys,
                }
                traintuple_key = create_traintuple(data, org_1)

                print('create second traintuple')
                data = {
                    'algo_key': algo_key_2,
                    'FLtask_key': '',
                    'input_models_keys': [],
                    'dataset_key': dataset_org1_key,
                    'train_data_keys': train_data_keys,
                }

                traintuple_key_2 = create_traintuple(data, org_1)

                data = {
                    'algo_key': algo_key_3,
                    'FLtask_key': '',
                    'input_models_keys': [],
                    'dataset_key': dataset_org1_key,
                    'train_data_keys': train_data_keys,
                }

                traintuple_key_3 = create_traintuple(data, org_1)

                ####################################################

                if traintuple_key:
                        res = popen(
                            ['substra', 'get', 'traintuple', traintuple_key,
                             f'--profile={org_1}',
                             '--config=/tmp/.substrabac'],
                            stdout=PIPE).communicate()[0]
                        res = json.loads(res.decode('utf-8'))
                        print(colored(json.dumps(res, indent=2), 'green'))

                        # create testtuple
                        print('create testtuple')
                        data = json.dumps({
                            'traintuple_key': traintuple_key
                        })

                        #testtuple_key = create_testuple(data, org_1)
                        testtuple_key = None

                        if testtuple_key:
                            res_tc = popen(
                                ['substra', 'get', 'testtuple', testtuple_key,
                                 f'--profile={org_1}',
                                 '--config=/tmp/.substrabac'],
                                stdout=PIPE).communicate()[0]
                            res_t = json.loads(res_tc.decode('utf-8'))
                            print(colored(json.dumps(res_t, indent=2), 'yellow'))

                            while res['result']['status'] not in ('done', 'failed') or res_t['result']['status'] not in ('done', 'failed'):
                                print('-' * 100)
                                try:
                                    resc = popen(['substra', 'get', 'traintuple', traintuple_key, f'--profile={org_1}', '--config=/tmp/.substrabac'],
                                                stdout=PIPE).communicate()[0]
                                    res = json.loads(resc.decode('utf-8'))
                                    print(colored(json.dumps(res, indent=2), 'green'))

                                    res_tc = popen(['substra', 'get', 'testtuple',
                                                   testtuple_key,
                                                   f'--profile={org_1}',
                                                   '--config=/tmp/.substrabac'],
                                                  stdout=PIPE).communicate()[0]
                                    res_t = json.loads(res_tc.decode('utf-8'))
                                    print(colored(json.dumps(res_t, indent=2), 'yellow'))
                                except:
                                    print(colored('Error when getting subtuples', 'red'))
                                time.sleep(3)

                        else:
                            while res['result']['status'] not in ('done', 'failed'):
                                print('-' * 100)
                                try:
                                    resc = popen(['substra', 'get', 'traintuple', traintuple_key, f'--profile={org_1}', '--config=/tmp/.substrabac'],
                                                stdout=PIPE).communicate()[0]
                                    res = json.loads(resc.decode('utf-8'))
                                    print(colored(json.dumps(res, indent=2), 'green'))
                                except:
                                    print(colored('Error when getting subtuple', 'red'))
                                time.sleep(3)

                            print('Testtuple create failed')
