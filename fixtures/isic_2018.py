import os
import json
from subprocess import PIPE, Popen as popen
import time

dir_path = os.path.dirname(os.path.realpath(__file__))

# Use substra shell SDK
try:
    popen(['substra'], stdout=PIPE).communicate()[0]
except BaseException:
    print('Substrabac SDK is not installed, please run pip install '
          'git+https://github.com/SubstraFoundation/substrabacSDK.git@master')
else:
    print('Init config in /tmp/.substrabac for owkin and chunantes')
    username = "owkestra"
    password = "owkestrapwd"
    auth = []
    if username is not None and password is not None:
        auth = [username, password]
    res = popen(['substra', 'config', 'https://substra.owkin.com:9000', '0.0',
                 '--profile=owkin', '--config=/tmp/.substrabac'] + auth,
                stdout=PIPE).communicate()[0]

    print('create data manager with owkin org')
    # create data manager with owkin org
    data = json.dumps({
        "name": "ISIC 2018",
        "data_opener": "/Users/kelvin/Substra/substra-challenge/skin-lesion-classification/dataset/isic2018/opener.py",
        "type": "Images",
        "description":
            "/Users/kelvin/Substra/substra-challenge/skin-lesion-classification/dataset/isic2018/description.md",
        "permissions": "all",
        "challenge_keys": []
    })

    res = popen(['substra', 'add', 'datamanager', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]
    res_data = json.loads(res.decode('utf-8'))
    datamanager_key = res_data['pkhash']
    print(json.dumps(res_data, indent=2))

    # Register Data on substrabac docker

    print('You have to register data manually')
    input("When it is done, press Enter to continue...")

    # register objective
    print('register objective')
    data = json.dumps({
        "name": "Skin Lesion Classification Objective",
        "description": "/Users/kelvin/Substra/substra-challenge/skin-lesion-classification/description.md",
        "metrics_name": "macro-average recall",
        "metrics": "/Users/kelvin/Substra/substra-challenge/skin-lesion-classification/metrics.py",
        "permissions": "all",
        "test_data_sample_keys": ["039eecf8279c570022f000984d91e175ca8efbf858f11b8bffc88d91ccb51096"]
    })

    res = popen(['substra', 'add', 'objective', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]
    res_data = json.loads(res.decode('utf-8'))
    objective_key = res_data['pkhash']
    print(json.dumps(res_data, indent=2))

    # ############################

    # register algo
    print('register algo')
    data = json.dumps({
        "name": "CNN Classifier GPU Updated",
        "file": "/Users/kelvin/Substra/substra-challenge/skin-lesion-classification/algo/algo.tar.gz",
        "description": "/Users/kelvin/Substra/substra-challenge/skin-lesion-classification/algo/description.md",
        "objective_key": objective_key,
        "permissions": "all",
    })

    res = popen(['substra', 'add', 'algo', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]
    res_data = json.loads(res.decode('utf-8'))
    algo_key = res_data['pkhash']
    print(json.dumps(res_data, indent=2))

    # ####################################

    # create traintuple
    print('create traintuple')
    data = json.dumps({
        "algo_key": algo_key,
        "model_key": "",
        "train_data_keys": ["33d577a1dbbf95c9cfccc4853ad7ca369b535243053f84a206308ad46e89aa59"]
    })

    res = popen(['substra', 'add', 'traintuple', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]
    res_data = json.loads(res.decode('utf-8'))
    trainuple_key = res_data['pkhash']
    print(json.dumps(res_data, indent=2))

    # Check traintuple
    res = popen(['substra', 'get', 'traintuple', trainuple_key, '--profile=owkin', '--config=/tmp/.substrabac'],
                stdout=PIPE).communicate()[0]
    res = json.loads(res.decode('utf-8'))
    print(json.dumps(res, indent=2))
    while res['status'] != 'done':
        res = popen(['substra', 'get', 'traintuple', trainuple_key, '--profile=owkin', '--config=/tmp/.substrabac'],
                    stdout=PIPE).communicate()[0]
        res = json.loads(res.decode('utf-8'))
        print(json.dumps(res, indent=2))
        time.sleep(3)
