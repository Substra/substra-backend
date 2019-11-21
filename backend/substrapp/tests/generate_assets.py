import argparse
import os
import json
import substra


dir_path = os.path.dirname(__file__)
assets_path = os.path.join(dir_path, 'assets.py')


def main(network):

    client = substra.Client()
    if network == 'docker':
        client.add_profile('default', 'substra', 'p@$swr0d44', 'http://substra-backend.owkin.xyz', '0.0')
    elif network == 'skaffold':
        client.add_profile('default', 'node-1', 'p@$swr0d44', 'http://substra-backend.node-1.com', '0.0')
    else:
        raise Exception('Unknow network')

    client.login()
    client.set_profile('default')

    assets = {}
    assets['objective'] = json.dumps(client.list_objective(), indent=4)
    assets['datamanager'] = json.dumps(client.list_dataset(), indent=4)
    assets['algo'] = json.dumps(client.list_algo(), indent=4)
    assets['traintuple'] = json.dumps(client.list_traintuple(), indent=4)
    assets['testtuple'] = json.dumps(client.list_testtuple(), indent=4)
    assets['computeplan'] = json.dumps(client.list_compute_plan(), indent=4)
    assets['compositetraintuple'] = """
[
    {
        "key": "363f70dcc3bf22fdce65e36c957e855b7cd3e2828e6909f34ccc97ee6218541a",
        "algo": {
            "name": "Composite Algo",
            "hash": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe441444",
            "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe441444/file/"
        },
        "creator": "chu-nantesMSP",
        "dataset": {
            "worker": "chu-nantesMSP",
            "keys": [
                "dacc0288138cb50569250f996bbe716ec8968fb334d32f29f174c9e79a224127",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 0
        },
        "computePlanID": "",
        "inHeadModelKey": "363f70dcc3bf22fdce65e36c957e855b7cd3e2828e6909f34ccc97ee6218541a",
        "inTrunkModelKey": "363f70dcc3bf22fdce65e36c957e855b7cd3e2828e6909f34ccc97ee6218541a",
        "log": "[00-01-0032-e18ebeb]",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "506dacd8800c36e70ad3df7379c9164e03452d700bd2c3edb472e6bd0dc01f2e",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outHeadModelKey": None,
        "outTrunkModelKey": None,
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "rank": 0,
        "status": "failed",
        "tag": "My super tag"
    },
    {
        "key": "05b44fa4b94d548e35922629f7b23dd84f777d09925bbecb0362081ca528f746",
        "algo": {
            "name": "Composite Algo",
            "hash": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe441444",
            "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe441444/file/"
        },
        "creator": "chu-nantesMSP",
        "dataset": {
            "worker": "chu-nantesMSP",
            "keys": [
                "dacc0288138cb50569250f996bbe716ec8968fb334d32f29f174c9e79a224127",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 1
        },
        "computePlanID": "",
        "inHeadModelKey": None,
        "inTrunkModelKey": None,
        "log": "",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "506dacd8800c36e70ad3df7379c9164e03452d700bd2c3edb472e6bd0dc01f2e",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outHeadModel": {
            "hash": "e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff99",
            "storageAddress": "http://testserver/model/e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff99/file/",
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": ["e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff22"]
                }
            }
        },
        "outTrunkModel": {
            "hash": "e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff99",
            "storageAddress": "http://testserver/model/e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff99/file/",
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff22",
                        "e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff23",
                        "e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff24"
                    ]
                }
            }
        },
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "rank": 0,
        "status": "done",
        "tag": "substra"
    },
    {
        "key": "32070e156eb4f97d85ff8448ea2ab71f4f275ab845159029354e4446aff974e0",
        "algo": {
            "name": "Composite Algo",
            "hash": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe441444",
            "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe441444/file/"
        },
        "creator": "chu-nantesMSP",
        "dataset": {
            "worker": "chu-nantesMSP",
            "keys": [
                "dacc0288138cb50569250f996bbe716ec8968fb334d32f29f174c9e79a224127",
                "e3644123451975be20909fcfd9c664a0573d9bfe04c5021625412d78c3536f1c"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 1
        },
        "computePlanID": "32070e156eb4f97d85ff8448ea2ab71f4f275ab845159029354e4446aff974e0",
        "inHeadModelKey": None,
        "inTrunkModelKey": None,
        "log": "",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "506dacd8800c36e70ad3df7379c9164e03452d700bd2c3edb472e6bd0dc01f2e",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outHeadModel": {
            "hash": "0b1ce6f2bd9247a262c3695aa07aad5ef187197f118c73c60a42e176f8f53b98",
            "storageAddress": "http://testserver/model/0b1ce6f2bd9247a262c3695aa07aad5ef187197f118c73c60a42e176f8f53b98/file/",
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": ["e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff22"]
                }
            }
        },
        "outTrunkModel": {
            "hash": "0b1ce6f2bd9247a262c3695aa07aad5ef187197f118c73c60a42e176f8f53b98",
            "storageAddress": "http://testserver/model/0b1ce6f2bd9247a262c3695aa07aad5ef187197f118c73c60a42e176f8f53b98/file/",
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff22",
                        "e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff23",
                        "e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff24",
                    ]
                }
            }
        },
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "rank": 0,
        "status": "done",
        "tag": ""
    },
    {
        "key": "a2171a1c09738c677748346d22d2b5eea47f874a3b4f4b75224674235892de72",
        "algo": {
            "name": "Composite Algo 2",
            "hash": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee4455",
            "storageAddress": "http://testserver/compositealgo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee4455/file/"
        },
        "creator": "chu-nantesMSP",
        "dataset": {
            "worker": "chu-nantesMSP",
            "keys": [
                "dacc0288138cb50569250f996bbe716ec8968fb334d32f29f174c9e79a224127",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 0
        },
        "computePlanID": "",
        "inHeadModelKey": None,
        "inTrunkModelKey": None,
        "log": "[00-01-0032-8189cc5]",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "506dacd8800c36e70ad3df7379c9164e03452d700bd2c3edb472e6bd0dc01f2e",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outHeadModel": None,
        "outTrunkModel": None,
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "rank": 0,
        "status": "failed",
        "tag": ""
    }
]
"""
    assets['compositealgo'] = """
[
    {
        "key": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9",
        "name": "Composite Algo",
        "content": {
            "hash": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9",
            "storageAddress": "http://testserver/compositealgo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9/file/"
        },
        "description": {
            "hash": "b9463411a01ea00869bdffce6e59a5c100a4e635c0a9386266cad3c77eb28e9e",
            "storageAddress": "http://testserver/compositealgo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9/description/"
        },
        "owner": "chu-nantesMSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        }
    },
    {
        "key": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee4455",
        "name": "Composite Algo 2",
        "content": {
            "hash": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee4455",
            "storageAddress": "http://testserver/compositealgo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee4455/file/"
        },
        "description": {
            "hash": "4acea40c4b51996c88ef279c5c9aa41ab77b97d38c5ca167e978a98b2e402675",
            "storageAddress": "http://testserver/compositealgo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee4455/description/"
        },
        "owner": "chu-nantesMSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        }
    }
]
"""

    assets['model'] = json.dumps([res for res in client.client.list('model')
                                  if ('traintuple' in res and 'testtuple' in res)], indent=4)

    with open(assets_path, 'w') as f:
        f.write('"""\nWARNING\n=======\n\nDO NOT MANUALLY EDIT THIS FILE!\n\n'
                'It is generated using substrapp/tests/generate_assets.py\n\n'
                'In order to update this file:\n'
                '1. start a clean instance of substra\n'
                '2. run populate.py\n'
                '3. run substrapp/tests/generate_assets.py\n"""\n\n')
        for k, v in assets.items():
            if network == 'docker':
                v = v.replace('substra-backend.owkin.xyz:8000', 'testserver')
                v = v.replace('substra-backend.chunantes.xyz:8001', 'testserver')
            if network == 'skaffold':
                v = v.replace('substra-backend.node-1.com', 'testserver')
                v = v.replace('substra-backend.node-2.com', 'testserver')
            v = v.replace('true', 'True')
            v = v.replace('false', 'False')
            v = v.replace('null', 'None')
            f.write(f'{k} = {v}')
            f.write('\n\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--skaffold', action='store_true',
                        help='Launch generate_assets with skaffold (K8S) network')

    args = parser.parse_args()
    network = 'skaffold' if args.skaffold else 'docker'

    main(network)
