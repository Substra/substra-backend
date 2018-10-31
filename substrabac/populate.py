import os
import json
from subprocess import PIPE, Popen as popen

dir_path = os.path.dirname(os.path.realpath(__file__))

# Use substra shell SDK
try:
    popen(['substra'], stdout=PIPE).communicate()[0]
except:
    print('Substrabac SDK is not installed, please run pip install git+https://github.com/SubstraFoundation/substrabacSDK.git@master')
else:

    print('Init config in /tmp/.substrabac for owkin and chunantes')
    res = popen(['substra', 'config', 'http://owkin.substrabac:8000', '0.0', '--profile=owkin',
                 '--config=/tmp/.substrabac'], stdout=PIPE).communicate()[0]
    res = popen(['substra', 'config', 'http://chunantes.substrabac:8001', '0.0', '--profile=chunantes',
                 '--config=/tmp/.substrabac'], stdout=PIPE).communicate()[0]

    print('create dataset with chu-nantes org')
    # create dataset with chu-nantes org
    data = json.dumps({
        "name": "ISIC 2018",
        "data_opener": os.path.join(dir_path, "./fixtures/chunantes/datasets/ccbaa3372bc74bce39ce3b138f558b3a7558958ef2f244576e18ed75b0cea994/opener.py"),
        "type": "Images",
        "description": os.path.join(dir_path, "./fixtures/chunantes/datasets/ccbaa3372bc74bce39ce3b138f558b3a7558958ef2f244576e18ed75b0cea994/description.md"),
        "permissions": "all",
        "challenge_keys": []
    })

    res = popen(['substra', 'add', 'dataset', '--profile=chunantes', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]
    print(json.dumps(json.loads(res.decode('utf-8')), indent=2))

    print('register train data on dataset chu nantes (will take dataset creator as worker)')
    # register train data on dataset chu nantes (will take dataset creator as worker)
    data = json.dumps({
        "files": [
            os.path.join(dir_path, "./fixtures/chunantes/data/62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a/0024700.zip"),
            os.path.join(dir_path, "./fixtures/chunantes/data/42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9/0024899.zip")
        ],
        "dataset_key": "ccbaa3372bc74bce39ce3b138f558b3a7558958ef2f244576e18ed75b0cea994",
        "test_only": False,
    })

    res = popen(['substra', 'add', 'data', data, '--profile=chunantes', '--config=/tmp/.substrabac'],
                stdout=PIPE).communicate()[0]
    print(json.dumps(json.loads(res.decode('utf-8')), indent=2))

    ###############################

    # create dataset, test data and challenge on owkin
    print('create dataset, test data and challenge on owkin')
    data = json.dumps({
        "name": "Simplified ISIC 2018",
        "data_opener": os.path.join(dir_path, "./fixtures/owkin/datasets/b4d2deeb9a59944d608e612abc8595c49186fa24075c4eb6f5e6050e4f9affa0/opener.py"),
        "type": "Images",
        "description": os.path.join(dir_path, "./fixtures/owkin/datasets/b4d2deeb9a59944d608e612abc8595c49186fa24075c4eb6f5e6050e4f9affa0/description.md"),
        "permissions": "all",
        "challenge_keys": []
    })

    res = popen(['substra', 'add', 'dataset', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]
    print(json.dumps(json.loads(res.decode('utf-8')), indent=2))

    #########################

    # register test data
    print('register test data')
    data = json.dumps({
        "files": [
            os.path.join(dir_path, "./fixtures/owkin/data/e11aeec290749e4c50c91305e10463eced8dbf3808971ec0c6ea0e36cb7ab3e1/0024900.zip"),
            os.path.join(dir_path, "./fixtures/owkin/data/4b5152871b181d10ee774c10458c064c70710f4ba35938f10c0b7aa51f7dc010/0024701.zip")
        ],
        "dataset_key": "b4d2deeb9a59944d608e612abc8595c49186fa24075c4eb6f5e6050e4f9affa0",
        "test_only": True,
    })

    res = popen(['substra', 'add', 'data', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]
    print(json.dumps(json.loads(res.decode('utf-8')), indent=2))

    #########################

    # register test data
    print('register test data')
    data = json.dumps({
        "files": [
            os.path.join(dir_path, "./fixtures/owkin/data/93e4b1e040b08cfa8a68b13f9dddb95a6672e8a377378545b2b1254691cfc060/0024317.zip"),
            os.path.join(dir_path, "./fixtures/owkin/data/eed4c6ea09babe7ca6428377fff6e54102ef5cdb0cae593732ddbe3f224217cb/0024316.zip")
        ],
        "dataset_key": "b4d2deeb9a59944d608e612abc8595c49186fa24075c4eb6f5e6050e4f9affa0",
        "test_only": True,
    })

    res = popen(['substra', 'add', 'data', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]
    print(json.dumps(json.loads(res.decode('utf-8')), indent=2))

    #########################

    # register test data
    print('register test data')
    data = json.dumps({
        "files": [
            os.path.join(dir_path, "./fixtures/owkin/data/2d0f943aa81a9cb3fe84b162559ce6aff068ccb04e0cb284733b8f9d7e06517e/0024315.zip"),
            os.path.join(dir_path, "./fixtures/owkin/data/533ee6e7b9d8b247e7e853b24547f57e6ef351852bac0418f13a0666173448f1/0024318.zip")
        ],
        "dataset_key": "b4d2deeb9a59944d608e612abc8595c49186fa24075c4eb6f5e6050e4f9affa0",
        "test_only": True,
    })

    res = popen(['substra', 'add', 'data', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]
    print(json.dumps(json.loads(res.decode('utf-8')), indent=2))

    # #########################

    # register challenge
    print('register challenge')
    data = json.dumps({
        "name": "Simplified skin lesion classification",
        "description": os.path.join(dir_path, "./fixtures/owkin/challenges/6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c/description.md"),
        "metrics_name": "macro-average recall",
        "metrics": os.path.join(dir_path, "./fixtures/owkin/challenges/6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c/metrics.py"),
        "permissions": "all",
        "test_data_keys": ["2d0f943aa81a9cb3fe84b162559ce6aff068ccb04e0cb284733b8f9d7e06517e",
                           "533ee6e7b9d8b247e7e853b24547f57e6ef351852bac0418f13a0666173448f1"]
    })

    res = popen(['substra', 'add', 'challenge', '--profile=owkin', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]
    print(json.dumps(json.loads(res.decode('utf-8')), indent=2))

    # register challenge
    print('register challenge')
    data = json.dumps({
        "name": "Skin Lesion Classification Challenge",
        "description": os.path.join(dir_path, "./fixtures/chunantes/challenges/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/description.md"),
        "metrics_name": "macro-average recall",
        "metrics": os.path.join(dir_path, "./fixtures/chunantes/challenges/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/metrics.py"),
        "permissions": "all",
        "test_data_keys": ["e11aeec290749e4c50c91305e10463eced8dbf3808971ec0c6ea0e36cb7ab3e1"]
    })

    res = popen(['substra', 'add', 'challenge', '--profile=chunantes', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]
    print(json.dumps(json.loads(res.decode('utf-8')), indent=2))

    ############################

    # register algo
    print('register algo')
    data = json.dumps({
        "name": "Logistic regression",
        "file": os.path.join(dir_path, "./fixtures/chunantes/algos/6dcbfcf29146acd19c6a2997b2e81d0cd4e88072eea9c90bbac33f0e8573993f/algo.tar.gz"),
        "description": os.path.join(dir_path, "./fixtures/chunantes/algos/6dcbfcf29146acd19c6a2997b2e81d0cd4e88072eea9c90bbac33f0e8573993f/description.md"),
        "challenge_key": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
        "permissions": "all",
    })

    res = popen(['substra', 'add', 'algo', '--profile=chunantes', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]
    print(json.dumps(json.loads(res.decode('utf-8')), indent=2))

    # register second algo on challenge Simplified skin lesion classification
    print('register second algo on challenge Simplified skin lesion classification')
    data = json.dumps({
        "name": "Logistic regression for balanced problem",
        "file": os.path.join(dir_path, "./fixtures/chunantes/algos/7742aea2001ceb40e9ce8a37fa27237d5b2d1f574e06d48677af945cfdf42ec0/algo.tar.gz"),
        "description": os.path.join(dir_path, "./fixtures/chunantes/algos/7742aea2001ceb40e9ce8a37fa27237d5b2d1f574e06d48677af945cfdf42ec0/description.md"),
        "challenge_key": "6b8d16ac3eae240743428591943fa8e66b34d4a7e0f4eb8e560485c7617c222c",
        "permissions": "all",
    })

    res = popen(['substra', 'add', 'algo', '--profile=chunantes', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]
    print(json.dumps(json.loads(res.decode('utf-8')), indent=2))

    # register third algo
    print('register third algo')
    data = json.dumps({
        "name": "Neural Network",
        "file": os.path.join(dir_path, "./fixtures/chunantes/algos/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/algo.tar.gz"),
        "description": os.path.join(dir_path, "./fixtures/chunantes/algos/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/description.md"),
        "challenge_key": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
        "permissions": "all",
    })

    res = popen(['substra', 'add', 'algo', '--profile=chunantes', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]
    print(json.dumps(json.loads(res.decode('utf-8')), indent=2))

    # register fourth algo
    print('register fourth algo')
    data = json.dumps({
        "name": "Random Forest",
        "file": os.path.join(dir_path, "./fixtures/chunantes/algos/f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284/algo.tar.gz"),
        "description": os.path.join(dir_path, "./fixtures/chunantes/algos/f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284/description.md"),
        "challenge_key": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
        "permissions": "all",
    })

    res = popen(['substra', 'add', 'algo', '--profile=chunantes', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]
    print(json.dumps(json.loads(res.decode('utf-8')), indent=2))
    ####################################

    # create traintuple
    print('create traintuple')
    data = json.dumps({
        "algo_key": "6dcbfcf29146acd19c6a2997b2e81d0cd4e88072eea9c90bbac33f0e8573993f",
        "model_key": "",
        "train_data_keys": ["62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a",
                            "42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9"]
    })

    res = popen(['substra', 'add', 'traintuple', '--profile=chunantes', '--config=/tmp/.substrabac', data],
                stdout=PIPE).communicate()[0]
    print(json.dumps(json.loads(res.decode('utf-8')), indent=2))
