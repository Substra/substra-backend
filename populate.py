import argparse
import os
import json
import shutil
import time

import substra

from termcolor import colored

dir_path = os.path.dirname(os.path.realpath(__file__))

SUBSTRA_FOLDER = os.getenv('SUBSTRA_PATH', '/substra')
server_path = f'{SUBSTRA_FOLDER}/servermedias'

client = substra.Client()


def setup_config():
    print('Init config in /tmp/.substrabac for owkin and chunantes')
    client.add_profile('owkin', 'http://owkin.substrabac:8000', '0.0')
    client.add_profile('chunantes', 'http://chunantes.substrabac:8001', '0.0')
    client.add_profile('clb', 'http://clb.substrabac:8002', '0.0')


def get_or_create(data, profile, asset, dryrun=False, local=True):

    client.set_profile(profile)

    method_kwargs = {}
    if not local:
        method_kwargs['local'] = False

    method = getattr(client, f'add_{asset}')

    if dryrun:
        print('dryrun')
        try:
            r = method(data, dryrun=True, **method_kwargs)
        except substra.exceptions.AlreadyExists as e:
            r = e.response.json()
            print(colored(json.dumps(r, indent=2), 'cyan'))
        else:
            print(colored(json.dumps(r, indent=2), 'magenta'))

    print('real')
    try:
        r = method(data, **method_kwargs)

    except substra.exceptions.AlreadyExists as e:
        r = e.response.json()
        print(colored(json.dumps(r, indent=2), 'cyan'))
        key_or_keys = e.pkhash

    else:
        print(colored(json.dumps(r, indent=2), 'green'))
        key_or_keys = [x['pkhash'] for x in r] if isinstance(r, list) else r['pkhash']

    return key_or_keys


def update_datamanager(data_manager_key, data, profile):
    client.set_profile(profile)
    try:
        r = client.update_dataset(data_manager_key, data)

    except substra.exceptions.AlreadyExists as e:
        r = e.response.json()
        print(colored(json.dumps(r, indent=2), 'cyan'))

    except substra.exceptions.InvalidRequest as e:
        # FIXME if the data manager is already associated with the objective
        #       backend answer with a 400 and a raw error coming from the
        #       ledger.
        #       this case will be handled soon, with the fabric SDK.
        print(colored(str(e), 'red'))

    else:
        print(colored(json.dumps(r, indent=2), 'green'))


def do_populate():
    setup_config()

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-o', '--one-org', action='store_const', dest='nb_org', const=1,
                       help='Launch populate with one org')
    group.add_argument('-tw', '--two-orgs', action='store_const', dest='nb_org', const=2,
                       help='Launch populate with two orgs')
    group.add_argument('-th', '--three-orgs', action='store_const', dest='nb_org', const=3,
                       help='Launch populate with three orgs')
    parser.add_argument('-a', '--archive', action='store_true',
                        help='Launch populate with archive data samples only')
    parser.set_defaults(nb_org=2)
    args = vars(parser.parse_args())

    if args['nb_org'] == 1:
        org_0 = org_1 = org_2 = 'owkin'
    elif args['nb_org'] == 2:
        org_0 = org_2 = 'owkin'
        org_1 = 'chunantes'
    elif args['nb_org'] == 3:
        org_0 = 'owkin'
        org_1 = 'chunantes'
        org_2 = 'clb'
    else:
        raise Exception(f"Number of orgs {args['nb_org']} not in [1, 2, 3]")

    print(f'will create datamanager with {org_1}')
    # create datamanager with org1
    data = {
        'name': 'ISIC 2018',
        'data_opener': os.path.join(dir_path, './fixtures/chunantes/datamanagers/datamanager0/opener.py'),
        'type': 'Images',
        'description': os.path.join(dir_path, './fixtures/chunantes/datamanagers/datamanager0/description.md'),
        'permissions': 'all',
    }
    data_manager_org1_key = get_or_create(data, org_1, 'dataset', dryrun=True)

    ####################################################

    train_data_sample_keys = []

    if not args['archive']:
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
        train_data_sample_keys = get_or_create(data, org_1, 'data_sample', dryrun=True, local=False)
    else:
        print(f'register train data on datamanager {org_1} (will take datamanager creator as worker)')
        data = {
            'paths': [
                os.path.join(dir_path, './fixtures/chunantes/datasamples/train/0024306'),
                os.path.join(dir_path, './fixtures/chunantes/datasamples/train/0024307')
            ],
            'data_manager_keys': [data_manager_org1_key],
            'test_only': False,
        }
        train_data_sample_keys = get_or_create(data, org_1, 'data_sample', dryrun=True)

    ####################################################

    print(f'create datamanager, test data and objective on {org_0}')
    data = {
        'name': 'Simplified ISIC 2018',
        'data_opener': os.path.join(dir_path, './fixtures/owkin/datamanagers/datamanager0/opener.py'),
        'type': 'Images',
        'description': os.path.join(dir_path, './fixtures/owkin/datamanagers/datamanager0/description.md'),
        'permissions': 'all'
    }
    data_manager_org0_key = get_or_create(data, org_0, 'dataset')

    ####################################################

    print('register test data')
    data = {
        'paths': [
            os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024900'),
            os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024901')
        ],
        'data_manager_keys': [data_manager_org0_key],
        'test_only': True,
    }
    test_data_sample_keys = get_or_create(data, org_0, 'data_sample')

    ####################################################

    print('register test data 2')
    data = {
        'paths': [
            os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024902'),
            os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024903')
        ],
        'data_manager_keys': [data_manager_org0_key],
        'test_only': True,
    }
    get_or_create(data, org_0, 'data_sample')

    ####################################################

    print('register test data 3')
    data = {
        'paths': [
            os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024904'),
            os.path.join(dir_path, './fixtures/owkin/datasamples/test/0024905')
        ],
        'data_manager_keys': [data_manager_org0_key],
        'test_only': True,
    }
    get_or_create(data, org_0, 'data_sample')

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

    objective_key = get_or_create(data, org_0, 'objective', dryrun=True)

    ####################################################

    print('register objective without data manager and data sample')
    data = {
        'name': 'Skin Lesion Classification Objective',
        'description': os.path.join(dir_path, './fixtures/owkin/objectives/objective0/description.md'),
        'metrics_name': 'macro-average recall',
        'metrics': os.path.join(dir_path, './fixtures/owkin/objectives/objective0/metrics.py'),
        'permissions': 'all'
    }

    get_or_create(data, org_0, 'objective', dryrun=True)

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
    algo_key = get_or_create(data, org_2, 'algo')

    ####################################################

    print('register algo 2')
    data = {
        'name': 'Neural Network',
        'file': os.path.join(dir_path, './fixtures/chunantes/algos/algo0/algo.tar.gz'),
        'description': os.path.join(dir_path, './fixtures/chunantes/algos/algo0/description.md'),
        'permissions': 'all',
    }
    algo_key_2 = get_or_create(data, org_1, 'algo')

    ####################################################

    data = {
        'name': 'Random Forest',
        'file': os.path.join(dir_path, './fixtures/chunantes/algos/algo4/algo.tar.gz'),
        'description': os.path.join(dir_path, './fixtures/chunantes/algos/algo4/description.md'),
        'permissions': 'all',
    }
    algo_key_3 = get_or_create(data, org_1, 'algo')

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
    traintuple_key = get_or_create(data, org_1, 'traintuple')

    print('create second traintuple')
    data = {
        'algo_key': algo_key_2,
        'data_manager_key': data_manager_org1_key,
        'objective_key': objective_key,
        'train_data_sample_keys': train_data_sample_keys,
        'tag': 'My super tag'
    }

    get_or_create(data, org_1, 'traintuple')

    print('create third traintuple')
    data = {
        'algo_key': algo_key_3,
        'data_manager_key': data_manager_org1_key,
        'objective_key': objective_key,
        'train_data_sample_keys': train_data_sample_keys,
    }

    get_or_create(data, org_1, 'traintuple')

    ####################################################

    client.set_profile(org_1)
    res = client.get_traintuple(traintuple_key)
    print(colored(json.dumps(res, indent=2), 'green'))

    # create testtuple
    print('create testtuple')
    data = {
        'traintuple_key': traintuple_key
    }

    testtuple_key = get_or_create(data, org_1, 'testtuple')

    client.set_profile(org_1)
    res_t = client.get_testtuple(testtuple_key)
    print(colored(json.dumps(res_t, indent=2), 'yellow'))

    testtuple_status = None
    traintuple_status = None

    client.set_profile(org_1)

    while traintuple_status not in ('done', 'failed') or testtuple_status not in ('done', 'failed'):
        res = client.get_traintuple(traintuple_key)
        res_t = client.get_testtuple(testtuple_key)
        if traintuple_status != res['status'] or testtuple_status != res_t['status']:
            traintuple_status = res['status']
            testtuple_status = res_t['status']
            print('')
            print('-' * 100)
            print(colored(json.dumps(res, indent=2), 'green'))
            print(colored(json.dumps(res_t, indent=2), 'yellow'))
        else:
            print('.', end='', flush=True)

        time.sleep(3)


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
        exit(1)
