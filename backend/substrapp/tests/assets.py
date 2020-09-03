"""
WARNING
=======

DO NOT MANUALLY EDIT THIS FILE!

It is generated using substrapp/tests/generate_assets.py

In order to update this file:
1. start a clean instance of substra
2. run computation on it (with e2e tests for instance)
3. run substrapp/tests/generate_assets.py
"""

objective = [
    {
        "key": "48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_global - Objective 0",
        "description": {
            "hash": "48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8",
            "storageAddress": "http://testserver/objective/48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8/description/"
        },
        "metrics": {
            "name": "test metrics",
            "hash": "0d64f855e07524da60203067713ab08fd6e479a02ebcb70364b2c6a2a29367e1",
            "storageAddress": "http://testserver/objective/48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8/metrics/"
        },
        "owner": "MyOrg1MSP",
        "testDataset": {
            "dataManagerKey": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "dataSampleKeys": [
                "ffed4147fffff2f18130b7332c1460ecccd8e1378765c415b82b948c19e98a68"
            ],
            "metadata": {},
            "worker": ""
        },
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "metadata": {}
    },
    {
        "key": "b61067adc59fb1aabe21eab767d986cccccdcfd8c64ea90a0bef59999051cea3",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_global - Objective 1",
        "description": {
            "hash": "b61067adc59fb1aabe21eab767d986cccccdcfd8c64ea90a0bef59999051cea3",
            "storageAddress": "http://testserver/objective/b61067adc59fb1aabe21eab767d986cccccdcfd8c64ea90a0bef59999051cea3/description/"
        },
        "metrics": {
            "name": "test metrics",
            "hash": "1a61bea02e3e75f8197d682cbaa6110c9709fbfbd4f16964acc390c70e7a22fe",
            "storageAddress": "http://testserver/objective/b61067adc59fb1aabe21eab767d986cccccdcfd8c64ea90a0bef59999051cea3/metrics/"
        },
        "owner": "MyOrg2MSP",
        "testDataset": {
            "dataManagerKey": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
            "dataSampleKeys": [
                "edaa4ccdfc9bcadda859498fbb550a6e1fc6baf176389c3eb18afc8a382b4145"
            ],
            "metadata": {},
            "worker": ""
        },
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "metadata": {}
    }
]

datamanager = [
    {
        "objectiveKey": "48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8",
        "description": {
            "hash": "8acac2e3b700de1e27ee00b8cc0b49a883476d4234015658cbff7a701332a498",
            "storageAddress": "http://testserver/data_manager/e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204/description/"
        },
        "key": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
        "metadata": {},
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_global - Dataset 0",
        "opener": {
            "hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "storageAddress": "http://testserver/data_manager/e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204/opener/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "type": "Test"
    },
    {
        "objectiveKey": "b61067adc59fb1aabe21eab767d986cccccdcfd8c64ea90a0bef59999051cea3",
        "description": {
            "hash": "0b32ac306997ff74a6b24e79264133de33d841e546f3f88b26a18d46e18223d9",
            "storageAddress": "http://testserver/data_manager/aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02/description/"
        },
        "key": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
        "metadata": {},
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_global - Dataset 1",
        "opener": {
            "hash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
            "storageAddress": "http://testserver/data_manager/aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02/opener/"
        },
        "owner": "MyOrg2MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "type": "Test"
    }
]

algo = [
    {
        "key": "4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple - Algo 0",
        "content": {
            "hash": "4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be",
            "storageAddress": "http://testserver/algo/4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be/file/"
        },
        "description": {
            "hash": "22b9af671a660afd001b15c5a85edaa81dc42fbda7aef03f2fd76aa10d2e5151",
            "storageAddress": "http://testserver/algo/4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be/description/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "metadata": {}
    },
    {
        "key": "59eb383497c337e280f2d7c6805cb80bb623dfe581b6289eeee4fc62aefd9c30",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_federated_learning_workflow - Algo 0",
        "content": {
            "hash": "59eb383497c337e280f2d7c6805cb80bb623dfe581b6289eeee4fc62aefd9c30",
            "storageAddress": "http://testserver/algo/59eb383497c337e280f2d7c6805cb80bb623dfe581b6289eeee4fc62aefd9c30/file/"
        },
        "description": {
            "hash": "df548aab4b1a66e08021774e0b70e6f59b858ba41afa550396d213357326f891",
            "storageAddress": "http://testserver/algo/59eb383497c337e280f2d7c6805cb80bb623dfe581b6289eeee4fc62aefd9c30/description/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "metadata": {}
    },
    {
        "key": "e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_same_node - Algo 0",
        "content": {
            "hash": "e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8",
            "storageAddress": "http://testserver/algo/e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8/file/"
        },
        "description": {
            "hash": "851fc503e6136c86f4a0f4035aa6d59c44f017694757769b9b2d7d39a7f5dc3c",
            "storageAddress": "http://testserver/algo/e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8/description/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "metadata": {}
    },
    {
        "key": "ebbd8c65dfe07d826d692f806deceffd296e715fa4db9e652304180dd7ee293d",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_traintuple_execution_failure - Algo 0",
        "content": {
            "hash": "ebbd8c65dfe07d826d692f806deceffd296e715fa4db9e652304180dd7ee293d",
            "storageAddress": "http://testserver/algo/ebbd8c65dfe07d826d692f806deceffd296e715fa4db9e652304180dd7ee293d/file/"
        },
        "description": {
            "hash": "d0289ce5f4ec35ea5eff7dc76b36cdc93c90bc3d76f55a8707a701f699742292",
            "storageAddress": "http://testserver/algo/ebbd8c65dfe07d826d692f806deceffd296e715fa4db9e652304180dd7ee293d/description/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "metadata": {}
    },
    {
        "key": "c8efb021f79c5adc96e9ba8407c368a5a3e76f2b37164176059855cc9daae593",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_different_nodes - Algo 0",
        "content": {
            "hash": "c8efb021f79c5adc96e9ba8407c368a5a3e76f2b37164176059855cc9daae593",
            "storageAddress": "http://testserver/algo/c8efb021f79c5adc96e9ba8407c368a5a3e76f2b37164176059855cc9daae593/file/"
        },
        "description": {
            "hash": "9a56aa11bdb75a1b5c2641493d546d4a28ec4d9d60aa0df18f5c2a019f8518b7",
            "storageAddress": "http://testserver/algo/c8efb021f79c5adc96e9ba8407c368a5a3e76f2b37164176059855cc9daae593/description/"
        },
        "owner": "MyOrg2MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "metadata": {}
    }
]

traintuple = [
    {
        "key": "3169bb172502f67556a6f12b856a5d653441227842aded24ade6b7866d3b624d",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple - Algo 0",
            "hash": "4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be",
            "storageAddress": "http://testserver/algo/4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f"
            ],
            "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "computePlanID": "",
        "inModels": None,
        "log": "",
        "metadata": {},
        "outModel": {
            "hash": "940262c35a6b33c2b7c8811fa785899b00e287ffa05e3cb5a23c857e9c89c760",
            "storageAddress": "http://testserver/model/940262c35a6b33c2b7c8811fa785899b00e287ffa05e3cb5a23c857e9c89c760/file/"
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
        "key": "a9c586b72c9c11412b0c9f81d599651a964d04934bca9f1886dd2d084f438a70",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple - Algo 0",
            "hash": "4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be",
            "storageAddress": "http://testserver/algo/4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "5702a4f561da782735e2e5d7b03605ee7bdb27d6bfc3187965e64cc0603bc0e3"
            ],
            "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "computePlanID": "",
        "inModels": None,
        "log": "",
        "metadata": {},
        "outModel": {
            "hash": "f33d3c7a21e97f5f0edd636f3b313c6a7757cc458614e49da74d58af7fc0c4c2",
            "storageAddress": "http://testserver/model/f33d3c7a21e97f5f0edd636f3b313c6a7757cc458614e49da74d58af7fc0c4c2/file/"
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
        "key": "ea7180ccc125dcceff10400fd2943f1e02fc915262c67f19986b3a9edbd765fb",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple - Algo 0",
            "hash": "4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be",
            "storageAddress": "http://testserver/algo/4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135"
            ],
            "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "computePlanID": "",
        "inModels": None,
        "log": "",
        "metadata": {},
        "outModel": {
            "hash": "02ccc4eeb426f7bbfe746a06a4c63a2023a8f2ea2c72f92242cc5f7f1164383c",
            "storageAddress": "http://testserver/model/02ccc4eeb426f7bbfe746a06a4c63a2023a8f2ea2c72f92242cc5f7f1164383c/file/"
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
        "key": "137804ca8660878062e419e340efd2826ce0d528c47a40879e30cdc1e77da1b0",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_federated_learning_workflow - Algo 0",
            "hash": "59eb383497c337e280f2d7c6805cb80bb623dfe581b6289eeee4fc62aefd9c30",
            "storageAddress": "http://testserver/algo/59eb383497c337e280f2d7c6805cb80bb623dfe581b6289eeee4fc62aefd9c30/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg2MSP",
            "keys": [
                "26e52856b27261fc12e9615d5914027dc5986cd8bb37ccf1da4c7aa47b74a8ea",
                "704740917e35b36648b80d9826e1f24d2082bf113f1693ba08975c7c405cb01f",
                "88608067e903a7b5cbfed480e7c4ee9eaf7eb37994cb2fec045497f324508a33",
                "e453da42246d9be33204fa30fb91755b989bbdeee2559dd93e14f57b57d1847f"
            ],
            "openerHash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
            "metadata": {}
        },
        "computePlanID": "4a7f743fd9a5ccaa6f8366a10f92955486ab15116a1e43f6c1ba1b9504f6b157",
        "inModels": [
            {
                "traintupleKey": "49dedc3b4e763a2d09e39f4e5eee3d4910beee8b4e3ba666f9c6ef00f1632ec3",
                "hash": "714ee81465576b09f1e4c6e0f28e82189501c46ed36569c9867eff851a285888",
                "storageAddress": "http://testserver/model/714ee81465576b09f1e4c6e0f28e82189501c46ed36569c9867eff851a285888/file/"
            }
        ],
        "log": "",
        "metadata": {},
        "outModel": {
            "hash": "4672cd5a9e134a6f6c54144c3a8e8330b2147fa10264ca8e9fbac9b9075cacd0",
            "storageAddress": "http://backend-org-2-substra-backend-server.org-2:8000/model/4672cd5a9e134a6f6c54144c3a8e8330b2147fa10264ca8e9fbac9b9075cacd0/file/"
        },
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "rank": 1,
        "status": "done",
        "tag": "foo"
    },
    {
        "key": "49dedc3b4e763a2d09e39f4e5eee3d4910beee8b4e3ba666f9c6ef00f1632ec3",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_federated_learning_workflow - Algo 0",
            "hash": "59eb383497c337e280f2d7c6805cb80bb623dfe581b6289eeee4fc62aefd9c30",
            "storageAddress": "http://testserver/algo/59eb383497c337e280f2d7c6805cb80bb623dfe581b6289eeee4fc62aefd9c30/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f",
                "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135",
                "5702a4f561da782735e2e5d7b03605ee7bdb27d6bfc3187965e64cc0603bc0e3",
                "8524b404cc1b25314fce92b8c31da7b1c9f1bab2ffd48e2c28382730bf8fe49f"
            ],
            "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "computePlanID": "4a7f743fd9a5ccaa6f8366a10f92955486ab15116a1e43f6c1ba1b9504f6b157",
        "inModels": None,
        "log": "",
        "metadata": {},
        "outModel": {
            "hash": "714ee81465576b09f1e4c6e0f28e82189501c46ed36569c9867eff851a285888",
            "storageAddress": "http://testserver/model/714ee81465576b09f1e4c6e0f28e82189501c46ed36569c9867eff851a285888/file/"
        },
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "rank": 0,
        "status": "done",
        "tag": "foo"
    },
    {
        "key": "e623fe67c0dc4ed78d4e34f9f0fad0ac3a5fa7aafb819a3e1961f978d7540b2a",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_different_nodes - Algo 0",
            "hash": "c8efb021f79c5adc96e9ba8407c368a5a3e76f2b37164176059855cc9daae593",
            "storageAddress": "http://backend-org-2-substra-backend-server.org-2:8000/algo/c8efb021f79c5adc96e9ba8407c368a5a3e76f2b37164176059855cc9daae593/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg2MSP",
            "keys": [
                "26e52856b27261fc12e9615d5914027dc5986cd8bb37ccf1da4c7aa47b74a8ea",
                "704740917e35b36648b80d9826e1f24d2082bf113f1693ba08975c7c405cb01f",
                "88608067e903a7b5cbfed480e7c4ee9eaf7eb37994cb2fec045497f324508a33",
                "e453da42246d9be33204fa30fb91755b989bbdeee2559dd93e14f57b57d1847f"
            ],
            "openerHash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
            "metadata": {}
        },
        "computePlanID": "",
        "inModels": None,
        "log": "",
        "metadata": {},
        "outModel": {
            "hash": "d771446f0be15ebaa66db902f5a98a5005611de4ea44d3a5fe77c50ee34ff114",
            "storageAddress": "http://backend-org-2-substra-backend-server.org-2:8000/model/d771446f0be15ebaa66db902f5a98a5005611de4ea44d3a5fe77c50ee34ff114/file/"
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
        "key": "e3aab7fe0c51e970edecdfa1f780fd529e437d92603e66e57f230d926c7808b6",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_same_node - Algo 0",
            "hash": "e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8",
            "storageAddress": "http://testserver/algo/e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f",
                "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135",
                "5702a4f561da782735e2e5d7b03605ee7bdb27d6bfc3187965e64cc0603bc0e3",
                "8524b404cc1b25314fce92b8c31da7b1c9f1bab2ffd48e2c28382730bf8fe49f"
            ],
            "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "computePlanID": "",
        "inModels": None,
        "log": "",
        "metadata": {
            "foo": "bar"
        },
        "outModel": {
            "hash": "420ce592a42e0c78e644447173b54046163a2afeadd37227cef6866fc7d4c4f7",
            "storageAddress": "http://testserver/model/420ce592a42e0c78e644447173b54046163a2afeadd37227cef6866fc7d4c4f7/file/"
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
        "key": "fcdbcf06d54b634edfe2dd2d46cfe8d63076570394b7335fab6e6aac99b51909",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_same_node - Algo 0",
            "hash": "e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8",
            "storageAddress": "http://testserver/algo/e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f",
                "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135",
                "5702a4f561da782735e2e5d7b03605ee7bdb27d6bfc3187965e64cc0603bc0e3",
                "8524b404cc1b25314fce92b8c31da7b1c9f1bab2ffd48e2c28382730bf8fe49f"
            ],
            "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "computePlanID": "",
        "inModels": [
            {
                "traintupleKey": "e3aab7fe0c51e970edecdfa1f780fd529e437d92603e66e57f230d926c7808b6",
                "hash": "420ce592a42e0c78e644447173b54046163a2afeadd37227cef6866fc7d4c4f7",
                "storageAddress": "http://testserver/model/420ce592a42e0c78e644447173b54046163a2afeadd37227cef6866fc7d4c4f7/file/"
            }
        ],
        "log": "",
        "metadata": {},
        "outModel": {
            "hash": "7b3183a99222df2b18de11c8f767fdca2c7ebb0d4fa8bfe03c4f169cfea2aba2",
            "storageAddress": "http://testserver/model/7b3183a99222df2b18de11c8f767fdca2c7ebb0d4fa8bfe03c4f169cfea2aba2/file/"
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
        "key": "5e18aef8a6748b220c82532c39b297159704f0b2b602ab8e5c4e6e59f2ec6cba",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_traintuple_execution_failure - Algo 0",
            "hash": "ebbd8c65dfe07d826d692f806deceffd296e715fa4db9e652304180dd7ee293d",
            "storageAddress": "http://testserver/algo/ebbd8c65dfe07d826d692f806deceffd296e715fa4db9e652304180dd7ee293d/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f",
                "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135",
                "5702a4f561da782735e2e5d7b03605ee7bdb27d6bfc3187965e64cc0603bc0e3",
                "8524b404cc1b25314fce92b8c31da7b1c9f1bab2ffd48e2c28382730bf8fe49f"
            ],
            "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "computePlanID": "",
        "inModels": None,
        "log": "[00-01-0117-d64af6f]",
        "metadata": {},
        "outModel": None,
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

testtuple = [
    {
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuples_execution - Algo 0",
            "hash": "09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf",
            "storageAddress": "http://testserver/composite_algo/09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf/file/"
        },
        "certified": True,
        "computePlanID": "",
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "ffed4147fffff2f18130b7332c1460ecccd8e1378765c415b82b948c19e98a68"
            ],
            "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "perf": 32
        },
        "key": "8cd0eb9ae2349fc33b36ebb689963840bdfd3ffe4f24392d77dba85c4c087d02",
        "log": "",
        "metadata": {},
        "objective": {
            "hash": "48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8",
            "metrics": {
                "hash": "0d64f855e07524da60203067713ab08fd6e479a02ebcb70364b2c6a2a29367e1",
                "storageAddress": "http://testserver/objective/48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8/metrics/"
            }
        },
        "rank": 0,
        "status": "done",
        "tag": "bar",
        "traintupleKey": "2978ca1f7d5520ef42a82c86a2e24d5b00f04c73013febdb5ed35d32dc606e92",
        "traintupleType": "compositeTraintuple"
    },
    {
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
            "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
            "storageAddress": "http://testserver/composite_algo/fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87/file/"
        },
        "certified": True,
        "computePlanID": "",
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg2MSP",
            "keys": [
                "edaa4ccdfc9bcadda859498fbb550a6e1fc6baf176389c3eb18afc8a382b4145"
            ],
            "openerHash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
            "perf": 32
        },
        "key": "87e835650d84ca0cf26ac332bad4f4d732a30606505f57f1817fb6580f16adc5",
        "log": "",
        "metadata": {},
        "objective": {
            "hash": "b61067adc59fb1aabe21eab767d986cccccdcfd8c64ea90a0bef59999051cea3",
            "metrics": {
                "hash": "1a61bea02e3e75f8197d682cbaa6110c9709fbfbd4f16964acc390c70e7a22fe",
                "storageAddress": "http://backend-org-2-substra-backend-server.org-2:8000/objective/b61067adc59fb1aabe21eab767d986cccccdcfd8c64ea90a0bef59999051cea3/metrics/"
            }
        },
        "rank": 0,
        "status": "done",
        "tag": "",
        "traintupleKey": "3be92d96d1abdabfbe6a4ff612d70f7f867f450c38ea344bd98d0775bec826fd",
        "traintupleType": "compositeTraintuple"
    },
    {
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
            "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
            "storageAddress": "http://testserver/composite_algo/fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87/file/"
        },
        "certified": True,
        "computePlanID": "",
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "ffed4147fffff2f18130b7332c1460ecccd8e1378765c415b82b948c19e98a68"
            ],
            "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "perf": 32
        },
        "key": "6075c796cc470f1e1de7b98d8a4d28b19e48c1d662ee9bdb982c0354088d2f2a",
        "log": "",
        "metadata": {},
        "objective": {
            "hash": "48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8",
            "metrics": {
                "hash": "0d64f855e07524da60203067713ab08fd6e479a02ebcb70364b2c6a2a29367e1",
                "storageAddress": "http://testserver/objective/48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8/metrics/"
            }
        },
        "rank": 0,
        "status": "done",
        "tag": "",
        "traintupleKey": "5adbd24ea21cb23b1ffc65151038a62c97f2d745d7df0928e683707f15a09556",
        "traintupleType": "compositeTraintuple"
    },
    {
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_same_node - Algo 0",
            "hash": "e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8",
            "storageAddress": "http://testserver/algo/e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8/file/"
        },
        "certified": True,
        "computePlanID": "",
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "ffed4147fffff2f18130b7332c1460ecccd8e1378765c415b82b948c19e98a68"
            ],
            "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "perf": 2
        },
        "key": "e2f386a88a1702cecf0270742a31cdf0be4a9d9b083467679058d00aaff55ac4",
        "log": "",
        "metadata": {},
        "objective": {
            "hash": "48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8",
            "metrics": {
                "hash": "0d64f855e07524da60203067713ab08fd6e479a02ebcb70364b2c6a2a29367e1",
                "storageAddress": "http://testserver/objective/48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8/metrics/"
            }
        },
        "rank": 0,
        "status": "done",
        "tag": "",
        "traintupleKey": "e3aab7fe0c51e970edecdfa1f780fd529e437d92603e66e57f230d926c7808b6",
        "traintupleType": "traintuple"
    },
    {
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_different_nodes - Algo 0",
            "hash": "c8efb021f79c5adc96e9ba8407c368a5a3e76f2b37164176059855cc9daae593",
            "storageAddress": "http://backend-org-2-substra-backend-server.org-2:8000/algo/c8efb021f79c5adc96e9ba8407c368a5a3e76f2b37164176059855cc9daae593/file/"
        },
        "certified": True,
        "computePlanID": "",
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "ffed4147fffff2f18130b7332c1460ecccd8e1378765c415b82b948c19e98a68"
            ],
            "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "perf": 2
        },
        "key": "0599697085f343a8298ee3a87bd0000285e944fa4a05f541aa985d3eab50c04d",
        "log": "",
        "metadata": {},
        "objective": {
            "hash": "48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8",
            "metrics": {
                "hash": "0d64f855e07524da60203067713ab08fd6e479a02ebcb70364b2c6a2a29367e1",
                "storageAddress": "http://testserver/objective/48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8/metrics/"
            }
        },
        "rank": 0,
        "status": "done",
        "tag": "",
        "traintupleKey": "e623fe67c0dc4ed78d4e34f9f0fad0ac3a5fa7aafb819a3e1961f978d7540b2a",
        "traintupleType": "traintuple"
    }
]

computeplan = [
    {
        "computePlanID": "4a7f743fd9a5ccaa6f8366a10f92955486ab15116a1e43f6c1ba1b9504f6b157",
        "traintupleKeys": [
            "49dedc3b4e763a2d09e39f4e5eee3d4910beee8b4e3ba666f9c6ef00f1632ec3",
            "137804ca8660878062e419e340efd2826ce0d528c47a40879e30cdc1e77da1b0"
        ],
        "aggregatetupleKeys": None,
        "compositeTraintupleKeys": None,
        "testtupleKeys": None,
        "cleanModels": False,
        "tag": "",
        "metadata": {},
        "status": "done",
        "tupleCount": 2,
        "doneCount": 2,
        "IDToKey": {}
    }
]

compositetraintuple = [
    {
        "key": "2978ca1f7d5520ef42a82c86a2e24d5b00f04c73013febdb5ed35d32dc606e92",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuples_execution - Algo 0",
            "hash": "09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf",
            "storageAddress": "http://testserver/composite_algo/09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f",
                "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135",
                "5702a4f561da782735e2e5d7b03605ee7bdb27d6bfc3187965e64cc0603bc0e3",
                "8524b404cc1b25314fce92b8c31da7b1c9f1bab2ffd48e2c28382730bf8fe49f"
            ],
            "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "computePlanID": "",
        "inHeadModel": {
            "traintupleKey": "aa9be143edc6ef051ea255fd77bb54ba40c71bb39afa3ece502dd36782d02a71",
            "hash": "64c72dc39772e122ef552d10ff101ef6cee94935a84678a0125f7c3fd044dff8",
            "storageAddress": ""
        },
        "inTrunkModel": {
            "traintupleKey": "aa9be143edc6ef051ea255fd77bb54ba40c71bb39afa3ece502dd36782d02a71",
            "hash": "00009a1256f8ce55ed907221000035daf1ac28111b5a3a03289da2f0601edf8f",
            "storageAddress": "http://testserver/model/00009a1256f8ce55ed907221000035daf1ac28111b5a3a03289da2f0601edf8f/file/"
        },
        "log": "",
        "metadata": {},
        "outHeadModel": {
            "outModel": {
                "hash": "349b475ebd9458739af8685b8b75d7aeb1290209eabadad1b9b8afaa2b05c8d5"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "outTrunkModel": {
            "outModel": {
                "hash": "692e3f70b9ebfca3c2e51e2a92c18092cc24dda547debefd6eb4bdd38ca6d803",
                "storageAddress": "http://testserver/model/692e3f70b9ebfca3c2e51e2a92c18092cc24dda547debefd6eb4bdd38ca6d803/file/"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "rank": 0,
        "status": "done",
        "tag": ""
    },
    {
        "key": "aa9be143edc6ef051ea255fd77bb54ba40c71bb39afa3ece502dd36782d02a71",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuples_execution - Algo 0",
            "hash": "09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf",
            "storageAddress": "http://testserver/composite_algo/09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f",
                "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135",
                "5702a4f561da782735e2e5d7b03605ee7bdb27d6bfc3187965e64cc0603bc0e3",
                "8524b404cc1b25314fce92b8c31da7b1c9f1bab2ffd48e2c28382730bf8fe49f"
            ],
            "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "computePlanID": "",
        "inHeadModel": None,
        "inTrunkModel": None,
        "log": "",
        "metadata": {},
        "outHeadModel": {
            "outModel": {
                "hash": "64c72dc39772e122ef552d10ff101ef6cee94935a84678a0125f7c3fd044dff8"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "outTrunkModel": {
            "outModel": {
                "hash": "00009a1256f8ce55ed907221000035daf1ac28111b5a3a03289da2f0601edf8f",
                "storageAddress": "http://testserver/model/00009a1256f8ce55ed907221000035daf1ac28111b5a3a03289da2f0601edf8f/file/"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "rank": 0,
        "status": "done",
        "tag": ""
    },
    {
        "key": "2d3e98fbeafebf1995db3ab205b9f803b18a1be8b4af72e242faceee3dd7d224",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuple_execution_failure - Algo 0",
            "hash": "0fbb505a32ae8785c08d37fe7bf7476d7365c3a0cef7c6e05c61c06db3267593",
            "storageAddress": "http://testserver/composite_algo/0fbb505a32ae8785c08d37fe7bf7476d7365c3a0cef7c6e05c61c06db3267593/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f",
                "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135",
                "5702a4f561da782735e2e5d7b03605ee7bdb27d6bfc3187965e64cc0603bc0e3",
                "8524b404cc1b25314fce92b8c31da7b1c9f1bab2ffd48e2c28382730bf8fe49f"
            ],
            "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "computePlanID": "",
        "inHeadModel": None,
        "inTrunkModel": None,
        "log": "[00-01-0117-d390d32]",
        "metadata": {},
        "outHeadModel": {
            "outModel": None,
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "outTrunkModel": {
            "outModel": None,
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "rank": 0,
        "status": "failed",
        "tag": ""
    },
    {
        "key": "7dbd4b2ac9e81b6dedd775809e0903d8fa55ce2cb8094bd6c4c20c2b0448b716",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple_execution_failure - Algo 0",
            "hash": "5a9fc1032bd97c9ebaafeaf7d2e5d81f375f1ff8e13ad3000e43f135eb47810c",
            "storageAddress": "http://testserver/composite_algo/5a9fc1032bd97c9ebaafeaf7d2e5d81f375f1ff8e13ad3000e43f135eb47810c/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f"
            ],
            "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "computePlanID": "",
        "inHeadModel": None,
        "inTrunkModel": None,
        "log": "",
        "metadata": {},
        "outHeadModel": {
            "outModel": {
                "hash": "8b87222907027a470d6d99409b0de9a9ced07142d026ab875d6ddfdecf9db96d"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "outTrunkModel": {
            "outModel": {
                "hash": "fcfcaa4f3be73940006fc54566b2946fabd5ee677496a5dd43e4b8c0c3c3d54d",
                "storageAddress": "http://testserver/model/fcfcaa4f3be73940006fc54566b2946fabd5ee677496a5dd43e4b8c0c3c3d54d/file/"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "rank": 0,
        "status": "done",
        "tag": ""
    },
    {
        "key": "df3e19426496a5b8a79d8f1b96e52de9fe3a07b6a81a9b5d9a34a824d52c1841",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple_execution_failure - Algo 0",
            "hash": "5a9fc1032bd97c9ebaafeaf7d2e5d81f375f1ff8e13ad3000e43f135eb47810c",
            "storageAddress": "http://testserver/composite_algo/5a9fc1032bd97c9ebaafeaf7d2e5d81f375f1ff8e13ad3000e43f135eb47810c/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135"
            ],
            "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "computePlanID": "",
        "inHeadModel": None,
        "inTrunkModel": None,
        "log": "",
        "metadata": {},
        "outHeadModel": {
            "outModel": {
                "hash": "bffb89749a253de1d451a836748dc813035dbcacb01fb85911b97c577c10ea6d"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "outTrunkModel": {
            "outModel": {
                "hash": "682d31d9e95654ed0aaf81184136d87c7ff2a0046c3d24181508f112d58b330d",
                "storageAddress": "http://testserver/model/682d31d9e95654ed0aaf81184136d87c7ff2a0046c3d24181508f112d58b330d/file/"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "rank": 0,
        "status": "done",
        "tag": ""
    },
    {
        "key": "3197bd6c56bc47089864c76b47b6115eb3551901ba304722ce581561c37b0c7b",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
            "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
            "storageAddress": "http://testserver/composite_algo/fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f"
            ],
            "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "computePlanID": "",
        "inHeadModel": None,
        "inTrunkModel": None,
        "log": "",
        "metadata": {},
        "outHeadModel": {
            "outModel": {
                "hash": "7d7ed2eac5e822ea90058387dd35d1270639ecc4982a6d72b619b8659813163a"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "outTrunkModel": {
            "outModel": {
                "hash": "b312a262592aa7ed56a07d0eb02bec0548745eb7316d4ea86b3719b2497d8cb2",
                "storageAddress": "http://testserver/model/b312a262592aa7ed56a07d0eb02bec0548745eb7316d4ea86b3719b2497d8cb2/file/"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP",
                        "MyOrg2MSP"
                    ]
                }
            }
        },
        "rank": 0,
        "status": "done",
        "tag": ""
    },
    {
        "key": "3be92d96d1abdabfbe6a4ff612d70f7f867f450c38ea344bd98d0775bec826fd",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
            "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
            "storageAddress": "http://testserver/composite_algo/fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg2MSP",
            "keys": [
                "704740917e35b36648b80d9826e1f24d2082bf113f1693ba08975c7c405cb01f"
            ],
            "openerHash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
            "metadata": {}
        },
        "computePlanID": "",
        "inHeadModel": {
            "traintupleKey": "e7b96818eadcdce6940c16b388bbd264549646a45bb8ea75e8f218d224c18162",
            "hash": "3af8f86ed9fe07237497e52d1ced195d7e4752f7d130327929f96ea688d60a41",
            "storageAddress": ""
        },
        "inTrunkModel": {
            "traintupleKey": "9cb5582fc3e822b9ddabbf7479097df05381294e3559f31a35c20f2e46e4885c",
            "hash": "4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688",
            "storageAddress": "http://testserver/model/4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688/file/"
        },
        "log": "",
        "metadata": {},
        "outHeadModel": {
            "outModel": {
                "hash": "8b6a7f3b7feef0a2c157bf2acfd2596fd7815a0a69b0a41b7451bab47d022eaa"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg2MSP"
                    ]
                }
            }
        },
        "outTrunkModel": {
            "outModel": {
                "hash": "66392ca3e6a5935fb8e22a5ee5b8af31dbec5655ff087b98f071abf7e4f3ce74",
                "storageAddress": "http://backend-org-2-substra-backend-server.org-2:8000/model/66392ca3e6a5935fb8e22a5ee5b8af31dbec5655ff087b98f071abf7e4f3ce74/file/"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP",
                        "MyOrg2MSP"
                    ]
                }
            }
        },
        "rank": 0,
        "status": "done",
        "tag": ""
    },
    {
        "key": "5adbd24ea21cb23b1ffc65151038a62c97f2d745d7df0928e683707f15a09556",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
            "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
            "storageAddress": "http://testserver/composite_algo/fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135"
            ],
            "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "computePlanID": "",
        "inHeadModel": {
            "traintupleKey": "3197bd6c56bc47089864c76b47b6115eb3551901ba304722ce581561c37b0c7b",
            "hash": "7d7ed2eac5e822ea90058387dd35d1270639ecc4982a6d72b619b8659813163a",
            "storageAddress": ""
        },
        "inTrunkModel": {
            "traintupleKey": "9cb5582fc3e822b9ddabbf7479097df05381294e3559f31a35c20f2e46e4885c",
            "hash": "4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688",
            "storageAddress": "http://testserver/model/4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688/file/"
        },
        "log": "",
        "metadata": {},
        "outHeadModel": {
            "outModel": {
                "hash": "28a705e08e765569bd89262f821e1c7285e43fa1e82df2f833464b8ff890c7bd"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "outTrunkModel": {
            "outModel": {
                "hash": "14b7e3254896db4f43c582695c39d096f33e1390e3ecaa8b0e6e7619bf827044",
                "storageAddress": "http://testserver/model/14b7e3254896db4f43c582695c39d096f33e1390e3ecaa8b0e6e7619bf827044/file/"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP",
                        "MyOrg2MSP"
                    ]
                }
            }
        },
        "rank": 0,
        "status": "done",
        "tag": ""
    },
    {
        "key": "e7b96818eadcdce6940c16b388bbd264549646a45bb8ea75e8f218d224c18162",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
            "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
            "storageAddress": "http://testserver/composite_algo/fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg2MSP",
            "keys": [
                "26e52856b27261fc12e9615d5914027dc5986cd8bb37ccf1da4c7aa47b74a8ea"
            ],
            "openerHash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
            "metadata": {}
        },
        "computePlanID": "",
        "inHeadModel": None,
        "inTrunkModel": None,
        "log": "",
        "metadata": {},
        "outHeadModel": {
            "outModel": {
                "hash": "3af8f86ed9fe07237497e52d1ced195d7e4752f7d130327929f96ea688d60a41"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg2MSP"
                    ]
                }
            }
        },
        "outTrunkModel": {
            "outModel": {
                "hash": "cd8a895a9b604ccbb2e2bf9f081d0560bfd86f4a98beabd833d4c7c36f35cd9d",
                "storageAddress": "http://backend-org-2-substra-backend-server.org-2:8000/model/cd8a895a9b604ccbb2e2bf9f081d0560bfd86f4a98beabd833d4c7c36f35cd9d/file/"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP",
                        "MyOrg2MSP"
                    ]
                }
            }
        },
        "rank": 0,
        "status": "done",
        "tag": "substra"
    }
]

compositealgo = [
    {
        "key": "09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuples_execution - Algo 0",
        "content": {
            "hash": "09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf",
            "storageAddress": "http://testserver/composite_algo/09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf/file/"
        },
        "description": {
            "hash": "aa444b9dc8cac0c80263b3970ddc403757abc6bcb546eb322a1711f1b8ec294d",
            "storageAddress": "http://testserver/composite_algo/09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf/description/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "metadata": {}
    },
    {
        "key": "0fbb505a32ae8785c08d37fe7bf7476d7365c3a0cef7c6e05c61c06db3267593",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuple_execution_failure - Algo 0",
        "content": {
            "hash": "0fbb505a32ae8785c08d37fe7bf7476d7365c3a0cef7c6e05c61c06db3267593",
            "storageAddress": "http://testserver/composite_algo/0fbb505a32ae8785c08d37fe7bf7476d7365c3a0cef7c6e05c61c06db3267593/file/"
        },
        "description": {
            "hash": "6d184a2e6d8097cc55e4b435bbd5b9c6d7211274472585448411cd435149e941",
            "storageAddress": "http://testserver/composite_algo/0fbb505a32ae8785c08d37fe7bf7476d7365c3a0cef7c6e05c61c06db3267593/description/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "metadata": {}
    },
    {
        "key": "5a9fc1032bd97c9ebaafeaf7d2e5d81f375f1ff8e13ad3000e43f135eb47810c",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple_execution_failure - Algo 0",
        "content": {
            "hash": "5a9fc1032bd97c9ebaafeaf7d2e5d81f375f1ff8e13ad3000e43f135eb47810c",
            "storageAddress": "http://testserver/composite_algo/5a9fc1032bd97c9ebaafeaf7d2e5d81f375f1ff8e13ad3000e43f135eb47810c/file/"
        },
        "description": {
            "hash": "61cc1c0f3962bc4d60151041e02b55ca9788ea7a8a848dfc67f3fc3194b5a202",
            "storageAddress": "http://testserver/composite_algo/5a9fc1032bd97c9ebaafeaf7d2e5d81f375f1ff8e13ad3000e43f135eb47810c/description/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "metadata": {}
    },
    {
        "key": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
        "content": {
            "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
            "storageAddress": "http://testserver/composite_algo/fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87/file/"
        },
        "description": {
            "hash": "066d354d20dfa689cd5ca22f99445dc47589971c6d958bd6841beeae585f1054",
            "storageAddress": "http://testserver/composite_algo/fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87/description/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "metadata": {}
    }
]

model = [
    {
        "traintuple": {
            "key": "3169bb172502f67556a6f12b856a5d653441227842aded24ade6b7866d3b624d",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple - Algo 0",
                "hash": "4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be",
                "storageAddress": "http://testserver/algo/4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f"
                ],
                "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "computePlanID": "",
            "inModels": None,
            "log": "",
            "metadata": {},
            "outModel": {
                "hash": "940262c35a6b33c2b7c8811fa785899b00e287ffa05e3cb5a23c857e9c89c760",
                "storageAddress": "http://testserver/model/940262c35a6b33c2b7c8811fa785899b00e287ffa05e3cb5a23c857e9c89c760/file/"
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
        "testtuple": {
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
        },
        "nonCertifiedTesttuples": None
    },
    {
        "traintuple": {
            "key": "a9c586b72c9c11412b0c9f81d599651a964d04934bca9f1886dd2d084f438a70",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple - Algo 0",
                "hash": "4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be",
                "storageAddress": "http://testserver/algo/4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "5702a4f561da782735e2e5d7b03605ee7bdb27d6bfc3187965e64cc0603bc0e3"
                ],
                "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "computePlanID": "",
            "inModels": None,
            "log": "",
            "metadata": {},
            "outModel": {
                "hash": "f33d3c7a21e97f5f0edd636f3b313c6a7757cc458614e49da74d58af7fc0c4c2",
                "storageAddress": "http://testserver/model/f33d3c7a21e97f5f0edd636f3b313c6a7757cc458614e49da74d58af7fc0c4c2/file/"
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
        "testtuple": {
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
        },
        "nonCertifiedTesttuples": None
    },
    {
        "traintuple": {
            "key": "ea7180ccc125dcceff10400fd2943f1e02fc915262c67f19986b3a9edbd765fb",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple - Algo 0",
                "hash": "4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be",
                "storageAddress": "http://testserver/algo/4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135"
                ],
                "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "computePlanID": "",
            "inModels": None,
            "log": "",
            "metadata": {},
            "outModel": {
                "hash": "02ccc4eeb426f7bbfe746a06a4c63a2023a8f2ea2c72f92242cc5f7f1164383c",
                "storageAddress": "http://testserver/model/02ccc4eeb426f7bbfe746a06a4c63a2023a8f2ea2c72f92242cc5f7f1164383c/file/"
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
        "testtuple": {
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
        },
        "nonCertifiedTesttuples": None
    },
    {
        "traintuple": {
            "key": "137804ca8660878062e419e340efd2826ce0d528c47a40879e30cdc1e77da1b0",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_federated_learning_workflow - Algo 0",
                "hash": "59eb383497c337e280f2d7c6805cb80bb623dfe581b6289eeee4fc62aefd9c30",
                "storageAddress": "http://testserver/algo/59eb383497c337e280f2d7c6805cb80bb623dfe581b6289eeee4fc62aefd9c30/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg2MSP",
                "keys": [
                    "26e52856b27261fc12e9615d5914027dc5986cd8bb37ccf1da4c7aa47b74a8ea",
                    "704740917e35b36648b80d9826e1f24d2082bf113f1693ba08975c7c405cb01f",
                    "88608067e903a7b5cbfed480e7c4ee9eaf7eb37994cb2fec045497f324508a33",
                    "e453da42246d9be33204fa30fb91755b989bbdeee2559dd93e14f57b57d1847f"
                ],
                "openerHash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
                "metadata": {}
            },
            "computePlanID": "4a7f743fd9a5ccaa6f8366a10f92955486ab15116a1e43f6c1ba1b9504f6b157",
            "inModels": [
                {
                    "traintupleKey": "49dedc3b4e763a2d09e39f4e5eee3d4910beee8b4e3ba666f9c6ef00f1632ec3",
                    "hash": "714ee81465576b09f1e4c6e0f28e82189501c46ed36569c9867eff851a285888",
                    "storageAddress": "http://testserver/model/714ee81465576b09f1e4c6e0f28e82189501c46ed36569c9867eff851a285888/file/"
                }
            ],
            "log": "",
            "metadata": {},
            "outModel": {
                "hash": "4672cd5a9e134a6f6c54144c3a8e8330b2147fa10264ca8e9fbac9b9075cacd0",
                "storageAddress": "http://backend-org-2-substra-backend-server.org-2:8000/model/4672cd5a9e134a6f6c54144c3a8e8330b2147fa10264ca8e9fbac9b9075cacd0/file/"
            },
            "permissions": {
                "process": {
                    "public": True,
                    "authorizedIDs": []
                }
            },
            "rank": 1,
            "status": "done",
            "tag": "foo"
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
        },
        "nonCertifiedTesttuples": None
    },
    {
        "traintuple": {
            "key": "49dedc3b4e763a2d09e39f4e5eee3d4910beee8b4e3ba666f9c6ef00f1632ec3",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_federated_learning_workflow - Algo 0",
                "hash": "59eb383497c337e280f2d7c6805cb80bb623dfe581b6289eeee4fc62aefd9c30",
                "storageAddress": "http://testserver/algo/59eb383497c337e280f2d7c6805cb80bb623dfe581b6289eeee4fc62aefd9c30/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f",
                    "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135",
                    "5702a4f561da782735e2e5d7b03605ee7bdb27d6bfc3187965e64cc0603bc0e3",
                    "8524b404cc1b25314fce92b8c31da7b1c9f1bab2ffd48e2c28382730bf8fe49f"
                ],
                "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "computePlanID": "4a7f743fd9a5ccaa6f8366a10f92955486ab15116a1e43f6c1ba1b9504f6b157",
            "inModels": None,
            "log": "",
            "metadata": {},
            "outModel": {
                "hash": "714ee81465576b09f1e4c6e0f28e82189501c46ed36569c9867eff851a285888",
                "storageAddress": "http://testserver/model/714ee81465576b09f1e4c6e0f28e82189501c46ed36569c9867eff851a285888/file/"
            },
            "permissions": {
                "process": {
                    "public": True,
                    "authorizedIDs": []
                }
            },
            "rank": 0,
            "status": "done",
            "tag": "foo"
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
        },
        "nonCertifiedTesttuples": None
    },
    {
        "traintuple": {
            "key": "e623fe67c0dc4ed78d4e34f9f0fad0ac3a5fa7aafb819a3e1961f978d7540b2a",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_different_nodes - Algo 0",
                "hash": "c8efb021f79c5adc96e9ba8407c368a5a3e76f2b37164176059855cc9daae593",
                "storageAddress": "http://backend-org-2-substra-backend-server.org-2:8000/algo/c8efb021f79c5adc96e9ba8407c368a5a3e76f2b37164176059855cc9daae593/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg2MSP",
                "keys": [
                    "26e52856b27261fc12e9615d5914027dc5986cd8bb37ccf1da4c7aa47b74a8ea",
                    "704740917e35b36648b80d9826e1f24d2082bf113f1693ba08975c7c405cb01f",
                    "88608067e903a7b5cbfed480e7c4ee9eaf7eb37994cb2fec045497f324508a33",
                    "e453da42246d9be33204fa30fb91755b989bbdeee2559dd93e14f57b57d1847f"
                ],
                "openerHash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
                "metadata": {}
            },
            "computePlanID": "",
            "inModels": None,
            "log": "",
            "metadata": {},
            "outModel": {
                "hash": "d771446f0be15ebaa66db902f5a98a5005611de4ea44d3a5fe77c50ee34ff114",
                "storageAddress": "http://backend-org-2-substra-backend-server.org-2:8000/model/d771446f0be15ebaa66db902f5a98a5005611de4ea44d3a5fe77c50ee34ff114/file/"
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
        "testtuple": {
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_different_nodes - Algo 0",
                "hash": "c8efb021f79c5adc96e9ba8407c368a5a3e76f2b37164176059855cc9daae593",
                "storageAddress": "http://backend-org-2-substra-backend-server.org-2:8000/algo/c8efb021f79c5adc96e9ba8407c368a5a3e76f2b37164176059855cc9daae593/file/"
            },
            "certified": True,
            "computePlanID": "",
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "ffed4147fffff2f18130b7332c1460ecccd8e1378765c415b82b948c19e98a68"
                ],
                "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "perf": 2
            },
            "key": "0599697085f343a8298ee3a87bd0000285e944fa4a05f541aa985d3eab50c04d",
            "log": "",
            "metadata": {},
            "objective": {
                "hash": "48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8",
                "metrics": {
                    "hash": "0d64f855e07524da60203067713ab08fd6e479a02ebcb70364b2c6a2a29367e1",
                    "storageAddress": "http://testserver/objective/48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8/metrics/"
                }
            },
            "rank": 0,
            "status": "done",
            "tag": "",
            "traintupleKey": "e623fe67c0dc4ed78d4e34f9f0fad0ac3a5fa7aafb819a3e1961f978d7540b2a",
            "traintupleType": "traintuple"
        },
        "nonCertifiedTesttuples": None
    },
    {
        "traintuple": {
            "key": "e3aab7fe0c51e970edecdfa1f780fd529e437d92603e66e57f230d926c7808b6",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_same_node - Algo 0",
                "hash": "e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8",
                "storageAddress": "http://testserver/algo/e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f",
                    "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135",
                    "5702a4f561da782735e2e5d7b03605ee7bdb27d6bfc3187965e64cc0603bc0e3",
                    "8524b404cc1b25314fce92b8c31da7b1c9f1bab2ffd48e2c28382730bf8fe49f"
                ],
                "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "computePlanID": "",
            "inModels": None,
            "log": "",
            "metadata": {
                "foo": "bar"
            },
            "outModel": {
                "hash": "420ce592a42e0c78e644447173b54046163a2afeadd37227cef6866fc7d4c4f7",
                "storageAddress": "http://testserver/model/420ce592a42e0c78e644447173b54046163a2afeadd37227cef6866fc7d4c4f7/file/"
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
        "testtuple": {
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_same_node - Algo 0",
                "hash": "e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8",
                "storageAddress": "http://testserver/algo/e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8/file/"
            },
            "certified": True,
            "computePlanID": "",
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "ffed4147fffff2f18130b7332c1460ecccd8e1378765c415b82b948c19e98a68"
                ],
                "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "perf": 2
            },
            "key": "e2f386a88a1702cecf0270742a31cdf0be4a9d9b083467679058d00aaff55ac4",
            "log": "",
            "metadata": {},
            "objective": {
                "hash": "48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8",
                "metrics": {
                    "hash": "0d64f855e07524da60203067713ab08fd6e479a02ebcb70364b2c6a2a29367e1",
                    "storageAddress": "http://testserver/objective/48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8/metrics/"
                }
            },
            "rank": 0,
            "status": "done",
            "tag": "",
            "traintupleKey": "e3aab7fe0c51e970edecdfa1f780fd529e437d92603e66e57f230d926c7808b6",
            "traintupleType": "traintuple"
        },
        "nonCertifiedTesttuples": None
    },
    {
        "traintuple": {
            "key": "fcdbcf06d54b634edfe2dd2d46cfe8d63076570394b7335fab6e6aac99b51909",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_same_node - Algo 0",
                "hash": "e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8",
                "storageAddress": "http://testserver/algo/e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f",
                    "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135",
                    "5702a4f561da782735e2e5d7b03605ee7bdb27d6bfc3187965e64cc0603bc0e3",
                    "8524b404cc1b25314fce92b8c31da7b1c9f1bab2ffd48e2c28382730bf8fe49f"
                ],
                "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "computePlanID": "",
            "inModels": [
                {
                    "traintupleKey": "e3aab7fe0c51e970edecdfa1f780fd529e437d92603e66e57f230d926c7808b6",
                    "hash": "420ce592a42e0c78e644447173b54046163a2afeadd37227cef6866fc7d4c4f7",
                    "storageAddress": "http://testserver/model/420ce592a42e0c78e644447173b54046163a2afeadd37227cef6866fc7d4c4f7/file/"
                }
            ],
            "log": "",
            "metadata": {},
            "outModel": {
                "hash": "7b3183a99222df2b18de11c8f767fdca2c7ebb0d4fa8bfe03c4f169cfea2aba2",
                "storageAddress": "http://testserver/model/7b3183a99222df2b18de11c8f767fdca2c7ebb0d4fa8bfe03c4f169cfea2aba2/file/"
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
        "testtuple": {
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
        },
        "nonCertifiedTesttuples": None
    },
    {
        "traintuple": {
            "key": "5e18aef8a6748b220c82532c39b297159704f0b2b602ab8e5c4e6e59f2ec6cba",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_traintuple_execution_failure - Algo 0",
                "hash": "ebbd8c65dfe07d826d692f806deceffd296e715fa4db9e652304180dd7ee293d",
                "storageAddress": "http://testserver/algo/ebbd8c65dfe07d826d692f806deceffd296e715fa4db9e652304180dd7ee293d/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f",
                    "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135",
                    "5702a4f561da782735e2e5d7b03605ee7bdb27d6bfc3187965e64cc0603bc0e3",
                    "8524b404cc1b25314fce92b8c31da7b1c9f1bab2ffd48e2c28382730bf8fe49f"
                ],
                "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "computePlanID": "",
            "inModels": None,
            "log": "[00-01-0117-d64af6f]",
            "metadata": {},
            "outModel": None,
            "permissions": {
                "process": {
                    "public": True,
                    "authorizedIDs": []
                }
            },
            "rank": 0,
            "status": "failed",
            "tag": ""
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
        },
        "nonCertifiedTesttuples": None
    },
    {
        "compositeTraintuple": {
            "key": "2978ca1f7d5520ef42a82c86a2e24d5b00f04c73013febdb5ed35d32dc606e92",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuples_execution - Algo 0",
                "hash": "09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf",
                "storageAddress": "http://testserver/composite_algo/09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f",
                    "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135",
                    "5702a4f561da782735e2e5d7b03605ee7bdb27d6bfc3187965e64cc0603bc0e3",
                    "8524b404cc1b25314fce92b8c31da7b1c9f1bab2ffd48e2c28382730bf8fe49f"
                ],
                "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "computePlanID": "",
            "inHeadModel": {
                "traintupleKey": "aa9be143edc6ef051ea255fd77bb54ba40c71bb39afa3ece502dd36782d02a71",
                "hash": "64c72dc39772e122ef552d10ff101ef6cee94935a84678a0125f7c3fd044dff8",
                "storageAddress": ""
            },
            "inTrunkModel": {
                "traintupleKey": "aa9be143edc6ef051ea255fd77bb54ba40c71bb39afa3ece502dd36782d02a71",
                "hash": "00009a1256f8ce55ed907221000035daf1ac28111b5a3a03289da2f0601edf8f",
                "storageAddress": "http://testserver/model/00009a1256f8ce55ed907221000035daf1ac28111b5a3a03289da2f0601edf8f/file/"
            },
            "log": "",
            "metadata": {},
            "outHeadModel": {
                "outModel": {
                    "hash": "349b475ebd9458739af8685b8b75d7aeb1290209eabadad1b9b8afaa2b05c8d5"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorizedIDs": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "outTrunkModel": {
                "outModel": {
                    "hash": "692e3f70b9ebfca3c2e51e2a92c18092cc24dda547debefd6eb4bdd38ca6d803",
                    "storageAddress": "http://testserver/model/692e3f70b9ebfca3c2e51e2a92c18092cc24dda547debefd6eb4bdd38ca6d803/file/"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorizedIDs": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "rank": 0,
            "status": "done",
            "tag": ""
        },
        "testtuple": {
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuples_execution - Algo 0",
                "hash": "09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf",
                "storageAddress": "http://testserver/composite_algo/09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf/file/"
            },
            "certified": True,
            "computePlanID": "",
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "ffed4147fffff2f18130b7332c1460ecccd8e1378765c415b82b948c19e98a68"
                ],
                "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "perf": 32
            },
            "key": "8cd0eb9ae2349fc33b36ebb689963840bdfd3ffe4f24392d77dba85c4c087d02",
            "log": "",
            "metadata": {},
            "objective": {
                "hash": "48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8",
                "metrics": {
                    "hash": "0d64f855e07524da60203067713ab08fd6e479a02ebcb70364b2c6a2a29367e1",
                    "storageAddress": "http://testserver/objective/48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8/metrics/"
                }
            },
            "rank": 0,
            "status": "done",
            "tag": "",
            "traintupleKey": "2978ca1f7d5520ef42a82c86a2e24d5b00f04c73013febdb5ed35d32dc606e92",
            "traintupleType": "compositeTraintuple"
        },
        "nonCertifiedTesttuples": None
    },
    {
        "compositeTraintuple": {
            "key": "aa9be143edc6ef051ea255fd77bb54ba40c71bb39afa3ece502dd36782d02a71",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuples_execution - Algo 0",
                "hash": "09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf",
                "storageAddress": "http://testserver/composite_algo/09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f",
                    "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135",
                    "5702a4f561da782735e2e5d7b03605ee7bdb27d6bfc3187965e64cc0603bc0e3",
                    "8524b404cc1b25314fce92b8c31da7b1c9f1bab2ffd48e2c28382730bf8fe49f"
                ],
                "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "computePlanID": "",
            "inHeadModel": None,
            "inTrunkModel": None,
            "log": "",
            "metadata": {},
            "outHeadModel": {
                "outModel": {
                    "hash": "64c72dc39772e122ef552d10ff101ef6cee94935a84678a0125f7c3fd044dff8"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorizedIDs": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "outTrunkModel": {
                "outModel": {
                    "hash": "00009a1256f8ce55ed907221000035daf1ac28111b5a3a03289da2f0601edf8f",
                    "storageAddress": "http://testserver/model/00009a1256f8ce55ed907221000035daf1ac28111b5a3a03289da2f0601edf8f/file/"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorizedIDs": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "rank": 0,
            "status": "done",
            "tag": ""
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
        },
        "nonCertifiedTesttuples": None
    },
    {
        "compositeTraintuple": {
            "key": "2d3e98fbeafebf1995db3ab205b9f803b18a1be8b4af72e242faceee3dd7d224",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuple_execution_failure - Algo 0",
                "hash": "0fbb505a32ae8785c08d37fe7bf7476d7365c3a0cef7c6e05c61c06db3267593",
                "storageAddress": "http://testserver/composite_algo/0fbb505a32ae8785c08d37fe7bf7476d7365c3a0cef7c6e05c61c06db3267593/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f",
                    "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135",
                    "5702a4f561da782735e2e5d7b03605ee7bdb27d6bfc3187965e64cc0603bc0e3",
                    "8524b404cc1b25314fce92b8c31da7b1c9f1bab2ffd48e2c28382730bf8fe49f"
                ],
                "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "computePlanID": "",
            "inHeadModel": None,
            "inTrunkModel": None,
            "log": "[00-01-0117-d390d32]",
            "metadata": {},
            "outHeadModel": {
                "outModel": None,
                "permissions": {
                    "process": {
                        "public": False,
                        "authorizedIDs": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "outTrunkModel": {
                "outModel": None,
                "permissions": {
                    "process": {
                        "public": False,
                        "authorizedIDs": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "rank": 0,
            "status": "failed",
            "tag": ""
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
        },
        "nonCertifiedTesttuples": None
    },
    {
        "compositeTraintuple": {
            "key": "7dbd4b2ac9e81b6dedd775809e0903d8fa55ce2cb8094bd6c4c20c2b0448b716",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple_execution_failure - Algo 0",
                "hash": "5a9fc1032bd97c9ebaafeaf7d2e5d81f375f1ff8e13ad3000e43f135eb47810c",
                "storageAddress": "http://testserver/composite_algo/5a9fc1032bd97c9ebaafeaf7d2e5d81f375f1ff8e13ad3000e43f135eb47810c/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f"
                ],
                "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "computePlanID": "",
            "inHeadModel": None,
            "inTrunkModel": None,
            "log": "",
            "metadata": {},
            "outHeadModel": {
                "outModel": {
                    "hash": "8b87222907027a470d6d99409b0de9a9ced07142d026ab875d6ddfdecf9db96d"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorizedIDs": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "outTrunkModel": {
                "outModel": {
                    "hash": "fcfcaa4f3be73940006fc54566b2946fabd5ee677496a5dd43e4b8c0c3c3d54d",
                    "storageAddress": "http://testserver/model/fcfcaa4f3be73940006fc54566b2946fabd5ee677496a5dd43e4b8c0c3c3d54d/file/"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorizedIDs": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "rank": 0,
            "status": "done",
            "tag": ""
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
        },
        "nonCertifiedTesttuples": None
    },
    {
        "compositeTraintuple": {
            "key": "df3e19426496a5b8a79d8f1b96e52de9fe3a07b6a81a9b5d9a34a824d52c1841",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple_execution_failure - Algo 0",
                "hash": "5a9fc1032bd97c9ebaafeaf7d2e5d81f375f1ff8e13ad3000e43f135eb47810c",
                "storageAddress": "http://testserver/composite_algo/5a9fc1032bd97c9ebaafeaf7d2e5d81f375f1ff8e13ad3000e43f135eb47810c/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135"
                ],
                "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "computePlanID": "",
            "inHeadModel": None,
            "inTrunkModel": None,
            "log": "",
            "metadata": {},
            "outHeadModel": {
                "outModel": {
                    "hash": "bffb89749a253de1d451a836748dc813035dbcacb01fb85911b97c577c10ea6d"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorizedIDs": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "outTrunkModel": {
                "outModel": {
                    "hash": "682d31d9e95654ed0aaf81184136d87c7ff2a0046c3d24181508f112d58b330d",
                    "storageAddress": "http://testserver/model/682d31d9e95654ed0aaf81184136d87c7ff2a0046c3d24181508f112d58b330d/file/"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorizedIDs": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "rank": 0,
            "status": "done",
            "tag": ""
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
        },
        "nonCertifiedTesttuples": None
    },
    {
        "compositeTraintuple": {
            "key": "3197bd6c56bc47089864c76b47b6115eb3551901ba304722ce581561c37b0c7b",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
                "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
                "storageAddress": "http://testserver/composite_algo/fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e2639598c42bbf9aba8d223c6a5d6cc1ad5066254b908eb49ac1e43577f"
                ],
                "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "computePlanID": "",
            "inHeadModel": None,
            "inTrunkModel": None,
            "log": "",
            "metadata": {},
            "outHeadModel": {
                "outModel": {
                    "hash": "7d7ed2eac5e822ea90058387dd35d1270639ecc4982a6d72b619b8659813163a"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorizedIDs": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "outTrunkModel": {
                "outModel": {
                    "hash": "b312a262592aa7ed56a07d0eb02bec0548745eb7316d4ea86b3719b2497d8cb2",
                    "storageAddress": "http://testserver/model/b312a262592aa7ed56a07d0eb02bec0548745eb7316d4ea86b3719b2497d8cb2/file/"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorizedIDs": [
                            "MyOrg1MSP",
                            "MyOrg2MSP"
                        ]
                    }
                }
            },
            "rank": 0,
            "status": "done",
            "tag": ""
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
        },
        "nonCertifiedTesttuples": None
    },
    {
        "compositeTraintuple": {
            "key": "3be92d96d1abdabfbe6a4ff612d70f7f867f450c38ea344bd98d0775bec826fd",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
                "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
                "storageAddress": "http://testserver/composite_algo/fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg2MSP",
                "keys": [
                    "704740917e35b36648b80d9826e1f24d2082bf113f1693ba08975c7c405cb01f"
                ],
                "openerHash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
                "metadata": {}
            },
            "computePlanID": "",
            "inHeadModel": {
                "traintupleKey": "e7b96818eadcdce6940c16b388bbd264549646a45bb8ea75e8f218d224c18162",
                "hash": "3af8f86ed9fe07237497e52d1ced195d7e4752f7d130327929f96ea688d60a41",
                "storageAddress": ""
            },
            "inTrunkModel": {
                "traintupleKey": "9cb5582fc3e822b9ddabbf7479097df05381294e3559f31a35c20f2e46e4885c",
                "hash": "4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688",
                "storageAddress": "http://testserver/model/4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688/file/"
            },
            "log": "",
            "metadata": {},
            "outHeadModel": {
                "outModel": {
                    "hash": "8b6a7f3b7feef0a2c157bf2acfd2596fd7815a0a69b0a41b7451bab47d022eaa"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorizedIDs": [
                            "MyOrg2MSP"
                        ]
                    }
                }
            },
            "outTrunkModel": {
                "outModel": {
                    "hash": "66392ca3e6a5935fb8e22a5ee5b8af31dbec5655ff087b98f071abf7e4f3ce74",
                    "storageAddress": "http://backend-org-2-substra-backend-server.org-2:8000/model/66392ca3e6a5935fb8e22a5ee5b8af31dbec5655ff087b98f071abf7e4f3ce74/file/"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorizedIDs": [
                            "MyOrg1MSP",
                            "MyOrg2MSP"
                        ]
                    }
                }
            },
            "rank": 0,
            "status": "done",
            "tag": ""
        },
        "testtuple": {
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
                "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
                "storageAddress": "http://testserver/composite_algo/fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87/file/"
            },
            "certified": True,
            "computePlanID": "",
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg2MSP",
                "keys": [
                    "edaa4ccdfc9bcadda859498fbb550a6e1fc6baf176389c3eb18afc8a382b4145"
                ],
                "openerHash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
                "perf": 32
            },
            "key": "87e835650d84ca0cf26ac332bad4f4d732a30606505f57f1817fb6580f16adc5",
            "log": "",
            "metadata": {},
            "objective": {
                "hash": "b61067adc59fb1aabe21eab767d986cccccdcfd8c64ea90a0bef59999051cea3",
                "metrics": {
                    "hash": "1a61bea02e3e75f8197d682cbaa6110c9709fbfbd4f16964acc390c70e7a22fe",
                    "storageAddress": "http://backend-org-2-substra-backend-server.org-2:8000/objective/b61067adc59fb1aabe21eab767d986cccccdcfd8c64ea90a0bef59999051cea3/metrics/"
                }
            },
            "rank": 0,
            "status": "done",
            "tag": "",
            "traintupleKey": "3be92d96d1abdabfbe6a4ff612d70f7f867f450c38ea344bd98d0775bec826fd",
            "traintupleType": "compositeTraintuple"
        },
        "nonCertifiedTesttuples": None
    },
    {
        "compositeTraintuple": {
            "key": "5adbd24ea21cb23b1ffc65151038a62c97f2d745d7df0928e683707f15a09556",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
                "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
                "storageAddress": "http://testserver/composite_algo/fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "51d906cc10b29eb81c935550b750811933bec25cb28ff88ea2549de2765db135"
                ],
                "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "computePlanID": "",
            "inHeadModel": {
                "traintupleKey": "3197bd6c56bc47089864c76b47b6115eb3551901ba304722ce581561c37b0c7b",
                "hash": "7d7ed2eac5e822ea90058387dd35d1270639ecc4982a6d72b619b8659813163a",
                "storageAddress": ""
            },
            "inTrunkModel": {
                "traintupleKey": "9cb5582fc3e822b9ddabbf7479097df05381294e3559f31a35c20f2e46e4885c",
                "hash": "4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688",
                "storageAddress": "http://testserver/model/4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688/file/"
            },
            "log": "",
            "metadata": {},
            "outHeadModel": {
                "outModel": {
                    "hash": "28a705e08e765569bd89262f821e1c7285e43fa1e82df2f833464b8ff890c7bd"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorizedIDs": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "outTrunkModel": {
                "outModel": {
                    "hash": "14b7e3254896db4f43c582695c39d096f33e1390e3ecaa8b0e6e7619bf827044",
                    "storageAddress": "http://testserver/model/14b7e3254896db4f43c582695c39d096f33e1390e3ecaa8b0e6e7619bf827044/file/"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorizedIDs": [
                            "MyOrg1MSP",
                            "MyOrg2MSP"
                        ]
                    }
                }
            },
            "rank": 0,
            "status": "done",
            "tag": ""
        },
        "testtuple": {
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
                "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
                "storageAddress": "http://testserver/composite_algo/fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87/file/"
            },
            "certified": True,
            "computePlanID": "",
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "ffed4147fffff2f18130b7332c1460ecccd8e1378765c415b82b948c19e98a68"
                ],
                "openerHash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "perf": 32
            },
            "key": "6075c796cc470f1e1de7b98d8a4d28b19e48c1d662ee9bdb982c0354088d2f2a",
            "log": "",
            "metadata": {},
            "objective": {
                "hash": "48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8",
                "metrics": {
                    "hash": "0d64f855e07524da60203067713ab08fd6e479a02ebcb70364b2c6a2a29367e1",
                    "storageAddress": "http://testserver/objective/48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8/metrics/"
                }
            },
            "rank": 0,
            "status": "done",
            "tag": "",
            "traintupleKey": "5adbd24ea21cb23b1ffc65151038a62c97f2d745d7df0928e683707f15a09556",
            "traintupleType": "compositeTraintuple"
        },
        "nonCertifiedTesttuples": None
    },
    {
        "compositeTraintuple": {
            "key": "e7b96818eadcdce6940c16b388bbd264549646a45bb8ea75e8f218d224c18162",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
                "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
                "storageAddress": "http://testserver/composite_algo/fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg2MSP",
                "keys": [
                    "26e52856b27261fc12e9615d5914027dc5986cd8bb37ccf1da4c7aa47b74a8ea"
                ],
                "openerHash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
                "metadata": {}
            },
            "computePlanID": "",
            "inHeadModel": None,
            "inTrunkModel": None,
            "log": "",
            "metadata": {},
            "outHeadModel": {
                "outModel": {
                    "hash": "3af8f86ed9fe07237497e52d1ced195d7e4752f7d130327929f96ea688d60a41"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorizedIDs": [
                            "MyOrg2MSP"
                        ]
                    }
                }
            },
            "outTrunkModel": {
                "outModel": {
                    "hash": "cd8a895a9b604ccbb2e2bf9f081d0560bfd86f4a98beabd833d4c7c36f35cd9d",
                    "storageAddress": "http://backend-org-2-substra-backend-server.org-2:8000/model/cd8a895a9b604ccbb2e2bf9f081d0560bfd86f4a98beabd833d4c7c36f35cd9d/file/"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorizedIDs": [
                            "MyOrg1MSP",
                            "MyOrg2MSP"
                        ]
                    }
                }
            },
            "rank": 0,
            "status": "done",
            "tag": ""
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
        },
        "nonCertifiedTesttuples": None
    },
    {
        "aggregatetuple": {
            "key": "9936e27a5738298e39e4308c0d4d612ada6ef1463bdbfe2b446b8e62230237a5",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple_execution_failure - Algo 1",
                "hash": "16acae7a5d702a97c4cce626bbe5c44d367d73617ee42e81660bce7494379986",
                "storageAddress": "http://testserver/aggregate_algo/16acae7a5d702a97c4cce626bbe5c44d367d73617ee42e81660bce7494379986/file/"
            },
            "creator": "MyOrg1MSP",
            "computePlanID": "",
            "log": "[00-01-0117-a45d457]",
            "metadata": {},
            "inModels": [
                {
                    "traintupleKey": "7dbd4b2ac9e81b6dedd775809e0903d8fa55ce2cb8094bd6c4c20c2b0448b716",
                    "hash": "fcfcaa4f3be73940006fc54566b2946fabd5ee677496a5dd43e4b8c0c3c3d54d",
                    "storageAddress": "http://testserver/model/fcfcaa4f3be73940006fc54566b2946fabd5ee677496a5dd43e4b8c0c3c3d54d/file/"
                },
                {
                    "traintupleKey": "df3e19426496a5b8a79d8f1b96e52de9fe3a07b6a81a9b5d9a34a824d52c1841",
                    "hash": "682d31d9e95654ed0aaf81184136d87c7ff2a0046c3d24181508f112d58b330d",
                    "storageAddress": "http://testserver/model/682d31d9e95654ed0aaf81184136d87c7ff2a0046c3d24181508f112d58b330d/file/"
                }
            ],
            "outModel": None,
            "rank": 0,
            "status": "failed",
            "tag": "",
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP"
                    ]
                }
            },
            "worker": "MyOrg1MSP"
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
        },
        "nonCertifiedTesttuples": None
    },
    {
        "aggregatetuple": {
            "key": "0c6d79470e536e7390623b37622228b507620e5878fe196112e23111168dcb38",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple - Algo 1",
                "hash": "25081cda2aab5915fe1d732c6483e24ef8fb2484a6e856c8ed912b36577d3d9a",
                "storageAddress": "http://testserver/aggregate_algo/25081cda2aab5915fe1d732c6483e24ef8fb2484a6e856c8ed912b36577d3d9a/file/"
            },
            "creator": "MyOrg1MSP",
            "computePlanID": "",
            "log": "",
            "metadata": {},
            "inModels": [
                {
                    "traintupleKey": "3169bb172502f67556a6f12b856a5d653441227842aded24ade6b7866d3b624d",
                    "hash": "940262c35a6b33c2b7c8811fa785899b00e287ffa05e3cb5a23c857e9c89c760",
                    "storageAddress": "http://testserver/model/940262c35a6b33c2b7c8811fa785899b00e287ffa05e3cb5a23c857e9c89c760/file/"
                },
                {
                    "traintupleKey": "ea7180ccc125dcceff10400fd2943f1e02fc915262c67f19986b3a9edbd765fb",
                    "hash": "02ccc4eeb426f7bbfe746a06a4c63a2023a8f2ea2c72f92242cc5f7f1164383c",
                    "storageAddress": "http://testserver/model/02ccc4eeb426f7bbfe746a06a4c63a2023a8f2ea2c72f92242cc5f7f1164383c/file/"
                },
                {
                    "traintupleKey": "a9c586b72c9c11412b0c9f81d599651a964d04934bca9f1886dd2d084f438a70",
                    "hash": "f33d3c7a21e97f5f0edd636f3b313c6a7757cc458614e49da74d58af7fc0c4c2",
                    "storageAddress": "http://testserver/model/f33d3c7a21e97f5f0edd636f3b313c6a7757cc458614e49da74d58af7fc0c4c2/file/"
                }
            ],
            "outModel": {
                "hash": "bd2e6a510edc11974e3d8b5459f0d4bd9b3169afe1fa47643147351f51fb18ac",
                "storageAddress": "http://testserver/model/bd2e6a510edc11974e3d8b5459f0d4bd9b3169afe1fa47643147351f51fb18ac/file/"
            },
            "rank": 0,
            "status": "done",
            "tag": "",
            "permissions": {
                "process": {
                    "public": True,
                    "authorizedIDs": []
                }
            },
            "worker": "MyOrg1MSP"
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
        },
        "nonCertifiedTesttuples": None
    },
    {
        "aggregatetuple": {
            "key": "9cb5582fc3e822b9ddabbf7479097df05381294e3559f31a35c20f2e46e4885c",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 1",
                "hash": "576485095a2f9bc78ed6238b847c9c679fb755b822c0cc6e08e60ea227ec0648",
                "storageAddress": "http://testserver/aggregate_algo/576485095a2f9bc78ed6238b847c9c679fb755b822c0cc6e08e60ea227ec0648/file/"
            },
            "creator": "MyOrg1MSP",
            "computePlanID": "",
            "log": "",
            "metadata": {},
            "inModels": [
                {
                    "traintupleKey": "3197bd6c56bc47089864c76b47b6115eb3551901ba304722ce581561c37b0c7b",
                    "hash": "b312a262592aa7ed56a07d0eb02bec0548745eb7316d4ea86b3719b2497d8cb2",
                    "storageAddress": "http://testserver/model/b312a262592aa7ed56a07d0eb02bec0548745eb7316d4ea86b3719b2497d8cb2/file/"
                },
                {
                    "traintupleKey": "e7b96818eadcdce6940c16b388bbd264549646a45bb8ea75e8f218d224c18162",
                    "hash": "cd8a895a9b604ccbb2e2bf9f081d0560bfd86f4a98beabd833d4c7c36f35cd9d",
                    "storageAddress": "http://backend-org-2-substra-backend-server.org-2:8000/model/cd8a895a9b604ccbb2e2bf9f081d0560bfd86f4a98beabd833d4c7c36f35cd9d/file/"
                }
            ],
            "outModel": {
                "hash": "4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688",
                "storageAddress": "http://testserver/model/4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688/file/"
            },
            "rank": 0,
            "status": "done",
            "tag": "",
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP",
                        "MyOrg2MSP"
                    ]
                }
            },
            "worker": "MyOrg1MSP"
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
        },
        "nonCertifiedTesttuples": None
    },
    {
        "aggregatetuple": {
            "key": "d57e8f3597a9c065d02c65c5a6def14b83a585a43223c227dad729b8e807e147",
            "algo": {
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 1",
                "hash": "576485095a2f9bc78ed6238b847c9c679fb755b822c0cc6e08e60ea227ec0648",
                "storageAddress": "http://testserver/aggregate_algo/576485095a2f9bc78ed6238b847c9c679fb755b822c0cc6e08e60ea227ec0648/file/"
            },
            "creator": "MyOrg1MSP",
            "computePlanID": "",
            "log": "",
            "metadata": {},
            "inModels": [
                {
                    "traintupleKey": "5adbd24ea21cb23b1ffc65151038a62c97f2d745d7df0928e683707f15a09556",
                    "hash": "14b7e3254896db4f43c582695c39d096f33e1390e3ecaa8b0e6e7619bf827044",
                    "storageAddress": "http://testserver/model/14b7e3254896db4f43c582695c39d096f33e1390e3ecaa8b0e6e7619bf827044/file/"
                },
                {
                    "traintupleKey": "3be92d96d1abdabfbe6a4ff612d70f7f867f450c38ea344bd98d0775bec826fd",
                    "hash": "66392ca3e6a5935fb8e22a5ee5b8af31dbec5655ff087b98f071abf7e4f3ce74",
                    "storageAddress": "http://backend-org-2-substra-backend-server.org-2:8000/model/66392ca3e6a5935fb8e22a5ee5b8af31dbec5655ff087b98f071abf7e4f3ce74/file/"
                }
            ],
            "outModel": {
                "hash": "d62bd637d4223726e96c46337539da3bbd94dc3a3b4f233f1c7152dd3b02364d",
                "storageAddress": "http://testserver/model/d62bd637d4223726e96c46337539da3bbd94dc3a3b4f233f1c7152dd3b02364d/file/"
            },
            "rank": 0,
            "status": "done",
            "tag": "",
            "permissions": {
                "process": {
                    "public": False,
                    "authorizedIDs": [
                        "MyOrg1MSP",
                        "MyOrg2MSP"
                    ]
                }
            },
            "worker": "MyOrg1MSP"
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
        },
        "nonCertifiedTesttuples": None
    }
]

