import argparse
import functools
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


def retry_until_success(f):
    """Retry request to substrabac in case of Timeout."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        delay = 1
        backoff = 2

        while True:
            try:
                return f(*args, **kwargs)
            except substra.exceptions.HTTPError as e:
                print(colored(e, 'red'))
                print(colored(e.response.content, 'red'))
                print(f'Request error: retrying in {delay}s')
                time.sleep(delay)
                delay *= backoff

    return wrapper


def create_asset(data, profile, asset, dryrun=False):
    client.set_config(profile)

    if dryrun:
        print('dryrun')
        try:
            r = client.add(asset, data, dryrun=True)
        except substra.exceptions.HTTPError as e:
            print(colored(e, 'red'))
        else:
            print(colored(json.dumps(r, indent=2), 'magenta'))

    print('real')
    try:
        r = client.add(asset, data)
    except substra.exceptions.HTTPError as e:
        if e.response.status_code == 408:
            # retry until success in case of timeout
            print(colored('got a 408, will test to get if from ledger', 'grey'))
            r = e.response.json()
            print(colored(json.dumps(r, indent=2), 'blue'))
            results = r['pkhash'] if 'pkhash' in r else r['message'].get('pkhash')

            keys_to_check = results if isinstance(results, list) else [results]
            for k in keys_to_check:
                retry_until_success(client.get)(asset, k)

            return results

        elif e.response.status_code == 409:
            r = e.response.json()
            print(colored(json.dumps(r, indent=2), 'cyan'))
            return [x['pkhash'] for x in r] if isinstance(r, list) else r['pkhash']

        else:
            print(colored(e, 'red'))
            try:
                error = e.response.json()
            except Exception:
                error = e.response
            else:
                print(colored(error, 'red'))
    else:
        print(colored(json.dumps(r, indent=2), 'green'))
        return [x['pkhash'] for x in r] if isinstance(r, list) else r['pkhash']


def register_asset(data, profile, asset, dryrun=False):
    client.set_config(profile)

    if dryrun:
        print('dryrun')
        try:
            r = client.register(asset, data, dryrun=True)
        except substra.exceptions.HTTPError as e:
            print(colored(e, 'red'))
        else:
            print(colored(json.dumps(r, indent=2), 'magenta'))

    print('real')
    try:
        r = client.register(asset, data)
    except substra.exceptions.HTTPError as e:
        if e.response.status_code == 408:
            # retry until success in case of timeout
            print(colored('got a 408, will test to get if from ledger', 'grey'))
            r = e.response.json()
            print(colored(json.dumps(r, indent=2), 'blue'))
            results = r['pkhash'] if 'pkhash' in r else r['message'].get('pkhash')

            keys_to_check = results if isinstance(results, list) else [results]
            for k in keys_to_check:
                retry_until_success(client.get)(asset, k)

            return results

        elif e.response.status_code == 409:
            r = e.response.json()
            print(colored(json.dumps(r, indent=2), 'cyan'))
            return [x['pkhash'] for x in r] if isinstance(r, list) else r['pkhash']

        else:
            print(colored(e, 'red'))
            try:
                error = e.response.json()
            except Exception:
                error = e.response
            else:
                print(colored(error, 'red'))
    else:
        print(colored(json.dumps(r, indent=2), 'green'))
        return [x['pkhash'] for x in r] if isinstance(r, list) else r['pkhash']


def update_datamanager(data_manager_key, data, profile):
    client.set_config(profile)

    try:
        r = client.update('data_manager', data_manager_key, data)
    except substra.exceptions.HTTPError as e:
        if e.response.status_code != 408:
            print(colored(e, 'red'))
            return None

        # retry until success in case of timeout
        r = retry_until_success(client.get)('data_manager', data_manager_key)
        print(colored(json.dumps(r, indent=2), 'cyan'))

    print(colored(json.dumps(r, indent=2), 'green'))
    return r['pkhash']


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
            'paths': [
                os.path.join(dir_path, './fixtures/chunantes/datasamples/train/0024306.zip'),
            ],
            'data_manager_keys': [data_manager_org1_key],
            'test_only': False,
        }
        train_data_sample_keys = create_asset(data, org_1, 'data_sample', True)

        print(f'register train data (from server) on datamanager {org_1} (will take datamanager creator as worker)')
        try:
            shutil.copytree(os.path.join(dir_path, './fixtures/chunantes/datasamples/train/0024308'),
                            os.path.join(server_path, './fixtures/chunantes/datasamples/train/0024308'))
        except FileExistsError:
            pass
        data = {
            'paths': [
                os.path.join(server_path, './fixtures/chunantes/datasamples/train/0024308')
            ],
            'data_manager_keys': [data_manager_org1_key],
            'test_only': False,
        }
        train_data_sample_keys = register_asset(data, org_1, 'data_sample', True)

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
            'paths': [
                os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024900.zip'),
                os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024901.zip')
            ],
            'data_manager_keys': [data_manager_org0_key],
            'test_only': True,
        }
        test_data_sample_keys = create_asset(data, org_0, 'data_sample', False)

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
        test_data_sample_keys_2 = create_asset(data, org_0, 'data_sample', False)

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
        test_data_sample_keys_3 = create_asset(data, org_0, 'data_sample', False)

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

        print('register objective without data manager and data sample')
        data = {
            'name': 'Skin Lesion Classification Objective',
            'description': os.path.join(dir_path, './fixtures/owkin/objectives/objective0/description.md'),
            'metrics_name': 'macro-average recall',
            'metrics': os.path.join(dir_path, './fixtures/owkin/objectives/objective0/metrics.py'),
            'permissions': 'all'
        }

        objective_key_test = create_asset(data, org_0, 'objective', True)

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
                'permissions': 'all',
            }
            algo_key = create_asset(data, org_1, 'algo', True)

            ####################################################

            print('register algo 2')
            data = {
                'name': 'Neural Network',
                'file': os.path.join(dir_path, './fixtures/chunantes/algos/algo0/algo.tar.gz'),
                'description': os.path.join(dir_path, './fixtures/chunantes/algos/algo0/description.md'),
                'permissions': 'all',
            }
            algo_key_2 = create_asset(data, org_1, 'algo', False)

            ####################################################

            data = {
                'name': 'Random Forest',
                'file': os.path.join(dir_path, './fixtures/chunantes/algos/algo4/algo.tar.gz'),
                'description': os.path.join(dir_path, './fixtures/chunantes/algos/algo4/description.md'),
                'permissions': 'all',
            }
            algo_key_3 = create_asset(data, org_1, 'algo', False)

            ####################################################

            if algo_key and train_data_sample_keys:
                # create traintuple
                print('create traintuple')
                data = {
                    'algo_key': algo_key,
                    'objective_key': objective_key,
                    'data_manager_key': data_manager_org1_key,
                    'train_data_sample_keys': train_data_sample_keys,
                    'tag': 'substra'
                }
                traintuple_key = create_asset(data, org_1, 'traintuple')

                print('create second traintuple')
                data = {
                    'algo_key': algo_key_2,
                    'data_manager_key': data_manager_org1_key,
                    'objective_key': objective_key,
                    'train_data_sample_keys': train_data_sample_keys,
                    'tag': 'My super tag'
                }

                traintuple_key_2 = create_asset(data, org_1, 'traintuple')

                print('create third traintuple')
                data = {
                    'algo_key': algo_key_3,
                    'data_manager_key': data_manager_org1_key,
                    'objective_key': objective_key,
                    'train_data_sample_keys': train_data_sample_keys,
                }

                traintuple_key_3 = create_asset(data, org_1, 'traintuple')

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

                    testtuple_key = create_asset(data, org_1, 'testtuple')
                    # testtuple_key = None

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
