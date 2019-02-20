import os
import json
import time
from subprocess import PIPE, Popen as popen

from django.conf import settings

dir_path = os.path.dirname(os.path.realpath(__file__))

# Use substra shell SDK
try:
    with open(os.devnull, 'w') as FNULL:
        popen(['substra'], stdout=FNULL, stderr=FNULL).communicate()[0]
except:
    print('Substrabac SDK is not installed, please run pip install git+https://github.com/SubstraFoundation/substrabacSDK.git@master')
else:

    print('Init config in /tmp/.substrabac for owkin')
    try:
        username = getattr(settings, 'BASICAUTH_USERNAME', None)
        password = getattr(settings, 'BASICAUTH_PASSWORD', None)

    except:
        username = None
        password = None
    auth = []
    if username is not None and password is not None:
            auth = [username, password]

    res = popen(['substra', 'config', 'http://owkin.substrabac:8000', '0.0', '--profile=owkin', '--config=/tmp/.substrabac'] + auth, stdout=PIPE).communicate()[0]

    print('create dataset with owkin org')
    # create dataset with owkin org
    data = json.dumps({
        'name': 'ISIC 2018',
        'data_opener': os.path.join(dir_path, './fixtures/chunantes/datasets/6ed251c2d71d99b206bf11e085e69c315e1861630655b3ce6fd55ca9513ef181/opener.py'),
        'type': 'Images',
        'description': os.path.join(dir_path, './fixtures/chunantes/datasets/6ed251c2d71d99b206bf11e085e69c315e1861630655b3ce6fd55ca9513ef181/description.md'),
        'permissions': 'all',
    })

    res = popen(['substra', 'add', 'dataset', '--profile=owkin', '--config=/tmp/.substrabac', data, '--dry-run'],
                stdout=PIPE).communicate()[0]

    try:
        print(json.dumps(json.loads(res.decode('utf-8')), indent=2))
    except:
        print(res.decode('utf-8'))

    res = popen(['substra', 'add', 'dataset', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]

    try:
        print(json.dumps(json.loads(res.decode('utf-8')), indent=2))
    except:
        print(res.decode('utf-8'))

    res_data = json.loads(res.decode('utf-8'))
    dataset_key = res_data['pkhash']

    print('register train data on dataset owkin (will take dataset creator as worker)')
    # register train data on dataset owkin (will take dataset creator as worker)
    data = json.dumps({
        'files': [
            os.path.join(dir_path, './fixtures/chunantes/data/62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a/0024700.zip'),
            os.path.join(dir_path, './fixtures/chunantes/data/42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9/0024899.zip')
        ],
        'dataset_keys': [dataset_key],
        'test_only': False,
    })

    res = popen(['substra', 'add', 'data', data, '--profile=owkin', '--config=/tmp/.substrabac'],
                stdout=PIPE).communicate()[0]

    try:
        print(json.dumps(json.loads(res.decode('utf-8')), indent=2))
    except:
        print(res.decode('utf-8'))

    res_data = json.loads(res.decode('utf-8'))
    try:
        data_key = [sub_res_data['pkhash'] for sub_res_data in res_data]
    except:
        data_key = res_data['pkhash']

    ###############################

    # create dataset, test data and challenge on owkin
    print('create dataset, test data and challenge on owkin')
    data = json.dumps({
        'name': 'Simplified ISIC 2018',
        'data_opener': os.path.join(dir_path, './fixtures/owkin/datasets/bcfdad31dbe9163e9f254a2b9a485f2dd5d035ecce4a1331788039f2bccdf7af/opener.py'),
        'type': 'Images',
        'description': os.path.join(dir_path, './fixtures/owkin/datasets/bcfdad31dbe9163e9f254a2b9a485f2dd5d035ecce4a1331788039f2bccdf7af/description.md'),
        'permissions': 'all'
    })

    res = popen(['substra', 'add', 'dataset', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]

    try:
        print(json.dumps(json.loads(res.decode('utf-8')), indent=2))
    except:
        print(res.decode('utf-8'))

    res_data = json.loads(res.decode('utf-8'))
    dataset_key_2 = res_data['pkhash']

    #########################

    # register test data
    print('register test data')
    data = json.dumps({
        'files': [
            os.path.join(dir_path, './fixtures/owkin/data/e11aeec290749e4c50c91305e10463eced8dbf3808971ec0c6ea0e36cb7ab3e1/0024900.zip'),
            os.path.join(dir_path, './fixtures/owkin/data/4b5152871b181d10ee774c10458c064c70710f4ba35938f10c0b7aa51f7dc010/0024701.zip')
        ],
        'dataset_keys': [dataset_key_2],
        'test_only': True,
    })

    res = popen(['substra', 'add', 'data', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]

    try:
        print(json.dumps(json.loads(res.decode('utf-8')), indent=2))
    except:
        print(res.decode('utf-8'))

    res_data = json.loads(res.decode('utf-8'))
    try:
        data_key_2_test = [sub_res_data['pkhash'] for sub_res_data in res_data]
    except:
        data_key_2_test = res_data['pkhash']


    #########################

    # register test data
    print('register test data')
    data = json.dumps({
        'files': [
            os.path.join(dir_path, './fixtures/owkin/data/93e4b1e040b08cfa8a68b13f9dddb95a6672e8a377378545b2b1254691cfc060/0024317.zip'),
            os.path.join(dir_path, './fixtures/owkin/data/eed4c6ea09babe7ca6428377fff6e54102ef5cdb0cae593732ddbe3f224217cb/0024316.zip')
        ],
        'dataset_keys': [dataset_key_2],
        'test_only': True,
    })

    res = popen(['substra', 'add', 'data', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]

    try:
        print(json.dumps(json.loads(res.decode('utf-8')), indent=2))
    except:
        print(res.decode('utf-8'))

    res_data = json.loads(res.decode('utf-8'))
    try:
        data_key_2_test_2 = [sub_res_data['pkhash'] for sub_res_data in res_data]
    except:
        data_key_2_test_2 = res_data['pkhash']

    #########################

    # register test data
    print('register test data')
    data = json.dumps({
        'files': [
            os.path.join(dir_path, './fixtures/owkin/data/2d0f943aa81a9cb3fe84b162559ce6aff068ccb04e0cb284733b8f9d7e06517e/0024315.zip'),
            os.path.join(dir_path, './fixtures/owkin/data/533ee6e7b9d8b247e7e853b24547f57e6ef351852bac0418f13a0666173448f1/0024318.zip')
        ],
        'dataset_keys': [dataset_key_2],
        'test_only': True,
    })

    res = popen(['substra', 'add', 'data', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]

    try:
        print(json.dumps(json.loads(res.decode('utf-8')), indent=2))
    except:
        print(res.decode('utf-8'))

    res_data = json.loads(res.decode('utf-8'))
    try:
        data_key_2_test_3 = [sub_res_data['pkhash'] for sub_res_data in res_data]
    except:
        data_key_2_test_3 = res_data['pkhash']

    # #########################

    # register challenge
    print('register challenge')
    data = json.dumps({
        'name': 'Skin Lesion Classification Challenge',
        'description': os.path.join(dir_path, './fixtures/chunantes/challenges/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/description.md'),
        'metrics_name': 'macro-average recall',
        'metrics': os.path.join(dir_path, './fixtures/chunantes/challenges/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/metrics.py'),
        'permissions': 'all',
        'test_data_keys': [data_key_2_test[0]],
        'test_dataset_key': dataset_key_2
    })

    res = popen(['substra', 'add', 'challenge', '--profile=owkin', '--config=/tmp/.substrabac', data, '--dry-run'],
                stdout=PIPE).communicate()[0]

    try:
        print(json.dumps(json.loads(res.decode('utf-8')), indent=2))
    except:
        print(res.decode('utf-8'))

    res = popen(['substra', 'add', 'challenge', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]

    try:
        print(json.dumps(json.loads(res.decode('utf-8')), indent=2))
    except:
        print(res.decode('utf-8'))

    res_data = json.loads(res.decode('utf-8'))
    challenge_key = res_data['pkhash']

    ############################

    # register algo
    print('register algo')
    data = json.dumps({
        'name': 'Logistic regression',
        'file': os.path.join(dir_path, './fixtures/chunantes/algos/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/algo.tar.gz'),
        'description': os.path.join(dir_path, './fixtures/chunantes/algos/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/description.md'),
        'challenge_key': challenge_key,
        'permissions': 'all',
    })

    res = popen(['substra', 'add', 'algo', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]

    try:
        print(json.dumps(json.loads(res.decode('utf-8')), indent=2))
    except:
        print(res.decode('utf-8'))

    res_data = json.loads(res.decode('utf-8'))
    algo_key = res_data['pkhash']

    # register second algo
    print('register second algo')
    data = json.dumps({
        'name': 'Neural Network',
        'file': os.path.join(dir_path, './fixtures/chunantes/algos/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/algo.tar.gz'),
        'description': os.path.join(dir_path, './fixtures/chunantes/algos/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/description.md'),
        'challenge_key': challenge_key,
        'permissions': 'all',
    })

    res = popen(['substra', 'add', 'algo', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]

    try:
        print(json.dumps(json.loads(res.decode('utf-8')), indent=2))
    except:
        print(res.decode('utf-8'))

    # register third algo
    print('register third algo')
    data = json.dumps({
        'name': 'Random Forest',
        'file': os.path.join(dir_path, './fixtures/chunantes/algos/f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284/algo.tar.gz'),
        'description': os.path.join(dir_path, './fixtures/chunantes/algos/f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284/description.md'),
        'challenge_key': challenge_key,
        'permissions': 'all',
    })

    res = popen(['substra', 'add', 'algo', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]

    try:
        print(json.dumps(json.loads(res.decode('utf-8')), indent=2))
    except:
        print(res.decode('utf-8'))
    ####################################

    # create traintuple
    print('create traintuple')
    data = json.dumps({
        'algo_key': algo_key,
        'FLtask_key': '',
        'model_key': '',
        'dataset_key': dataset_key,
        'train_data_keys': data_key,
    })

    res = popen(['substra', 'add', 'traintuple', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]

    try:
        print(json.dumps(json.loads(res.decode('utf-8')), indent=2))
    except:
        print(res.decode('utf-8'))
    else:
        res = json.loads(res.decode('utf-8'))
        if 'pkhash' in res:
            traintuple_key = res['pkhash']

            res = popen(['substra', 'get', 'traintuple', traintuple_key, '--profile=owkin', '--config=/tmp/.substrabac'],
                        stdout=PIPE).communicate()[0]
            res = json.loads(res.decode('utf-8'))
            print(json.dumps(res, indent=2))
            # while res['status'] not in ('done', 'failed'):
            #     res = popen(['substra', 'get', 'traintuple', traintuple_key, '--profile=owkin', '--config=/tmp/.substrabac'],
            #                 stdout=PIPE).communicate()[0]
            #     res = json.loads(res.decode('utf-8'))
            #     print(json.dumps(res, indent=2))
            #     time.sleep(3)
            #
            # if res['status'] == 'done':
            # create testtuple
            print('create testtuple')
            data = json.dumps({
                'traintuple_key': traintuple_key
            })

            res = popen(['substra', 'add', 'testtuple', '--profile=owkin', '--config=/tmp/.substrabac', data],
                        stdout=PIPE).communicate()[0]
            res = json.loads(res.decode('utf-8'))
            testtuple_key = res['pkhash']
            print(json.dumps(res, indent=2))

            res = popen(['substra', 'get', 'testtuple', testtuple_key, '--profile=owkin', '--config=/tmp/.substrabac'], stdout=PIPE).communicate()[0]
            res = json.loads(res.decode('utf-8'))

            while res['status'] not in ('done', 'failed'):
                res = popen(['substra', 'get', 'testtuple', testtuple_key, '--profile=owkin', '--config=/tmp/.substrabac'],
                      stdout=PIPE).communicate()[0]
                res = json.loads(res.decode('utf-8'))
                print(json.dumps(res, indent=2))
                time.sleep(3)
