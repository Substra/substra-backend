import os
import json
import time
from subprocess import PIPE, Popen as popen

from rest_framework import status

dir_path = os.path.dirname(os.path.realpath(__file__))


# Use substra cli
def setup_config():
    try:
        with open(os.devnull, 'w') as FNULL:
            popen(['substra'], stdout=FNULL, stderr=FNULL).communicate()[0]
    except:
        print('Substrabac SDK is not installed, please run pip install git+https://github.com/SubstraFoundation/substrabacSDK.git@master')
    else:
        print('Init config in /tmp/.substrabac for owkin and chunantes')
        popen(['substra', 'config', 'http://owkin.substrabac:8000', '0.0', '--profile=owkin',
                     '--config=/tmp/.substrabac'], stdout=PIPE).communicate()[0]
        popen(['substra', 'config', 'http://chunantes.substrabac:8001', '0.0', '--profile=chunantes',
                     '--config=/tmp/.substrabac'], stdout=PIPE).communicate()[0]


def create_asset(data, profile, asset, dryrun=False):
    if dryrun:
        print('dry-run')
        res = popen(['substra', 'add', asset, f'--profile={profile}', '--config=/tmp/.substrabac', data, '--dry-run'], stdout=PIPE).communicate()[0]
        try:
            print(json.dumps(json.loads(res.decode('utf-8')), indent=2))
        except:
            print(res.decode('utf-8'))

    print('real')
    res = popen(['substra', 'add', asset, f'--profile={profile}', '--config=/tmp/.substrabac', data], stdout=PIPE).communicate()[0]

    try:
        r = json.loads(res.decode('utf-8'))
    except:
        print(res.decode('utf-8'))
        return None
    else:
        print('result: ', json.dumps(r['result'], indent=2))

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
            print(json.dumps(r['result'], indent=2))

        return r['result']['pkhash']


def create_data(data, profile, dryrun=False):

    if dryrun:
        print('dry-run')
        res = popen(['substra', 'add', 'data', data, f'--profile={profile}', '--config=/tmp/.substrabac', '--dry-run'],
                    stdout=PIPE).communicate()[0]
        try:
            print(json.dumps(json.loads(res.decode('utf-8')), indent=2))
        except:
            print(res.decode('utf-8'))

    print('real')
    res = popen(['substra', 'add', 'data', data, f'--profile={profile}', '--config=/tmp/.substrabac'], stdout=PIPE).communicate()[0]

    try:
        r = json.loads(res.decode('utf-8'))
    except:
        print(res.decode('utf-8'))
        return None
    else:
        print('result: ', json.dumps(r['result'], indent=2))

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
                    print(json.dumps(r, indent=2))
                    print('.', end='')
                    time.sleep(1)
                print(json.dumps(r['result'], indent=2))

        return data_keys


def update_dataset(dataset_key, data, profile):

    res = popen(['substra', 'update', 'dataset', dataset_key, f'--profile={profile}',
                 '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]
    try:
        print(json.dumps(json.loads(res.decode('utf-8')), indent=2))
    except:
        print(res.decode('utf-8'))

    r = json.loads(res.decode('utf-8'))

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
            print(json.dumps(r, indent=2))
            print('.', end='')
            time.sleep(1)
        print(json.dumps(r['result'], indent=2))

    return r['result']['pkhash']


def create_traintuple(data, profile):
    res = popen(['substra', 'add', 'traintuple', f'--profile={profile}', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]

    try:
        r = json.loads(res.decode('utf-8'))
    except:
        print(res.decode('utf-8'))
        return None
    else:
        print('result: ', json.dumps(r['result'], indent=2))

        if r['status_code'] in (status.HTTP_400_BAD_REQUEST, status.HTTP_408_REQUEST_TIMEOUT):
            return None

        return r['result']


def create_testuple(data, profile):
        res = popen(['substra', 'add', 'testtuple', f'--profile={profile}', '--config=/tmp/.substrabac', data],
                    stdout=PIPE).communicate()[0]

        try:
            r = json.loads(res.decode('utf-8'))
        except:
            print(res.decode('utf-8'))
            return None
        else:
            print('result: ', json.dumps(r['result'], indent=2))

            if r['status_code'] in (status.HTTP_400_BAD_REQUEST, status.HTTP_408_REQUEST_TIMEOUT):
                return None

            return r['result']


if __name__ == '__main__':
    setup_config()

    print('will create dataset with chu-nantes org')
    # create dataset with chu-nantes org
    data = json.dumps({
        'name': 'ISIC 2018',
        'data_opener': os.path.join(dir_path, './fixtures/chunantes/datasets/6ed251c2d71d99b206bf11e085e69c315e1861630655b3ce6fd55ca9513ef181/opener.py'),
        'type': 'Images',
        'description': os.path.join(dir_path, './fixtures/chunantes/datasets/6ed251c2d71d99b206bf11e085e69c315e1861630655b3ce6fd55ca9513ef181/description.md'),
        'permissions': 'all',
    })
    dataset_chunantes_key = create_asset(data, 'chunantes', 'dataset', dryrun=True)

    ####################################################

    train_data_keys = []
    if dataset_chunantes_key:
        print('register train data on dataset chu-nantes (will take dataset creator as worker)')
        data = json.dumps({
            'files': [
                os.path.join(dir_path, './fixtures/chunantes/data/62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a/0024700.zip'),
                os.path.join(dir_path, './fixtures/chunantes/data/42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9/0024899.zip')
            ],
            'dataset_keys': [dataset_chunantes_key],
            'test_only': False,
        })
        train_data_keys = create_data(data, 'chunantes', True)

    ####################################################

    print('create dataset, test data and challenge on owkin')
    data = json.dumps({
        'name': 'Simplified ISIC 2018',
        'data_opener': os.path.join(dir_path, './fixtures/owkin/datasets/bcfdad31dbe9163e9f254a2b9a485f2dd5d035ecce4a1331788039f2bccdf7af/opener.py'),
        'type': 'Images',
        'description': os.path.join(dir_path, './fixtures/owkin/datasets/bcfdad31dbe9163e9f254a2b9a485f2dd5d035ecce4a1331788039f2bccdf7af/description.md'),
        'permissions': 'all'
    })
    dataset_owkin_key = create_asset(data, 'owkin', 'dataset')

    ####################################################

    if dataset_owkin_key:
        print('register test data')
        data = json.dumps({
            'files': [
                os.path.join(dir_path, './fixtures/owkin/data/e11aeec290749e4c50c91305e10463eced8dbf3808971ec0c6ea0e36cb7ab3e1/0024900.zip'),
                os.path.join(dir_path, './fixtures/owkin/data/4b5152871b181d10ee774c10458c064c70710f4ba35938f10c0b7aa51f7dc010/0024701.zip')
            ],
            'dataset_keys': [dataset_owkin_key],
            'test_only': True,
        })
        test_data_keys = create_data(data, 'owkin', False)

        ####################################################

        print('register test data 2')
        data = json.dumps({
            'files': [
                os.path.join(dir_path, './fixtures/owkin/data/93e4b1e040b08cfa8a68b13f9dddb95a6672e8a377378545b2b1254691cfc060/0024317.zip'),
                os.path.join(dir_path, './fixtures/owkin/data/eed4c6ea09babe7ca6428377fff6e54102ef5cdb0cae593732ddbe3f224217cb/0024316.zip')
            ],
            'dataset_keys': [dataset_owkin_key],
            'test_only': True,
        })
        test_data_keys_2 = create_data(data, 'owkin', False)

        ####################################################

        print('register test data 3')
        data = json.dumps({
            'files': [
                os.path.join(dir_path, './fixtures/owkin/data/2d0f943aa81a9cb3fe84b162559ce6aff068ccb04e0cb284733b8f9d7e06517e/0024315.zip'),
                os.path.join(dir_path,  './fixtures/owkin/data/533ee6e7b9d8b247e7e853b24547f57e6ef351852bac0418f13a0666173448f1/0024318.zip')
            ],
            'dataset_keys': [dataset_owkin_key],
            'test_only': True,
        })
        test_data_keys_3 = create_data(data, 'owkin', False)

        ####################################################

        print('register challenge')
        data = json.dumps({
            'name': 'Skin Lesion Classification Challenge',
            'description': os.path.join(dir_path, './fixtures/chunantes/challenges/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/description.md'),
            'metrics_name': 'macro-average recall',
            'metrics': os.path.join(dir_path,  './fixtures/chunantes/challenges/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/metrics.py'),
            'permissions': 'all',
            'test_data_keys': test_data_keys,
            'test_dataset_key': dataset_owkin_key
        })

        challenge_key = create_asset(data, 'owkin', 'challenge', True)

        ####################################################

        # update dataset
        print('update dataset')
        data = json.dumps({
            'challenge_key': challenge_key
        })
        update_dataset(dataset_chunantes_key, data, 'owkin')

        ####################################################

        if challenge_key:
            # register algo
            print('register algo')
            data = json.dumps({
                'name': 'Logistic regression',
                'file': os.path.join(dir_path, './fixtures/chunantes/algos/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/algo.tar.gz'),
                'description': os.path.join(dir_path, './fixtures/chunantes/algos/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/description.md'),
                'challenge_key': challenge_key,
                'permissions': 'all',
            })
            algo_key = create_asset(data, 'chunantes', 'algo', True)

            ####################################################

            print('register algo 2')
            data = json.dumps({
                'name': 'Neural Network',
                'file': os.path.join(dir_path, './fixtures/chunantes/algos/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/algo.tar.gz'),
                'description': os.path.join(dir_path, './fixtures/chunantes/algos/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/description.md'),
                'challenge_key': challenge_key,
                'permissions': 'all',
            })
            algo_key_2 = create_asset(data, 'chunantes', 'algo', False)

            ####################################################

            data = json.dumps({
                'name': 'Random Forest',
                'file': os.path.join(dir_path, './fixtures/chunantes/algos/f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284/algo.tar.gz'),
                'description': os.path.join(dir_path, './fixtures/chunantes/algos/f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284/description.md'),
                'challenge_key': challenge_key,
                'permissions': 'all',
            })
            algo_key_3 = create_asset(data, 'chunantes', 'algo', False)

            ####################################################

            if algo_key and train_data_keys:
                # create traintuple
                print('create traintuple')
                data = json.dumps({
                    'algo_key': algo_key,
                    'FLtask_key': '',
                    'model_key': '',
                    'dataset_key': dataset_chunantes_key,
                    'train_data_keys': train_data_keys,
                })
                traintuple = create_traintuple(data, 'chunantes')

                ####################################################

<<<<<<< HEAD
                if traintuple_key:
=======
                if traintuple and 'pkhash' in traintuple:
                        traintuple_key = traintuple['pkhash']

>>>>>>> update traintuple
                        res = popen(
                            ['substra', 'get', 'traintuple', traintuple['pkhash'],
                             '--profile=chunantes',
                             '--config=/tmp/.substrabac'],
                            stdout=PIPE).communicate()[0]
                        res = json.loads(res.decode('utf-8'))
                        print(json.dumps(res, indent=2))
                        while res['result']['status'] not in ('done', 'failed'):
                            res = popen(['substra', 'get', 'traintuple', traintuple_key, '--profile=chunantes', '--config=/tmp/.substrabac'],
                                  stdout=PIPE).communicate()[0]
                            res = json.loads(res.decode('utf-8'))
                            print(json.dumps(res, indent=2))
                            time.sleep(3)

                        ####################################################

                        if res['result']['status'] == 'done':
                            # create testtuple
                            print('create testtuple')
                            data = json.dumps({
                                'traintuple_key': traintuple_key
                            })

                            testtuple_key = create_testuple(data, 'chunantes')

                            if testtuple_key:
                                res = popen(
                                    ['substra', 'get', 'testtuple', testtuple_key,
                                     '--profile=chunantes',
                                     '--config=/tmp/.substrabac'],
                                    stdout=PIPE).communicate()[0]
                                res = json.loads(res.decode('utf-8'))

                                while res['result']['status'] not in ('done', 'failed'):
                                    res = popen(['substra', 'get', 'testtuple',
                                                 testtuple_key,
                                                 '--profile=chunantes',
                                                 '--config=/tmp/.substrabac'],
                                                stdout=PIPE).communicate()[0]
                                    res = json.loads(res.decode('utf-8'))
                                    print(json.dumps(res, indent=2))
                                    time.sleep(3)
