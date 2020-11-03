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
        "key": "48cc5ce4-d352-b859-e202-adb0d639ee09",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_global - Objective 0",
        "description": {
            "hash": "48cc5ce4d352b859e202adb0d639ee092c78cae7a2a1df0fccd88c63b3466ad8",
            "storage_address": "http://testserver/objective/48cc5ce4-d352-b859-e202-adb0d639ee09/description/"
        },
        "metrics": {
            "name": "test metrics",
            "hash": "0d64f855e07524da60203067713ab08fd6e479a02ebcb70364b2c6a2a29367e1",
            "storage_address": "http://testserver/objective/48cc5ce4-d352-b859-e202-adb0d639ee09/metrics/"
        },
        "owner": "MyOrg1MSP",
        "test_dataset": {
            "data_manager_key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "data_sample_keys": [
                "ffed4147-ffff-f2f1-8130-b7332c1460ec"
            ],
            "metadata": {},
            "worker": ""
        },
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "metadata": {}
    },
    {
        "key": "b61067ad-c59f-b1aa-be21-eab767d986cc",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_global - Objective 1",
        "description": {
            "hash": "b61067adc59fb1aabe21eab767d986cccccdcfd8c64ea90a0bef59999051cea3",
            "storage_address": "http://testserver/objective/b61067ad-c59f-b1aa-be21-eab767d986cc/description/"
        },
        "metrics": {
            "name": "test metrics",
            "hash": "1a61bea02e3e75f8197d682cbaa6110c9709fbfbd4f16964acc390c70e7a22fe",
            "storage_address": "http://testserver/objective/b61067ad-c59f-b1aa-be21-eab767d986cc/metrics/"
        },
        "owner": "MyOrg2MSP",
        "test_dataset": {
            "data_manager_key": "aa572a96-4b02-4435-d48a-73aacb86e3d1",
            "data_sample_keys": [
                "edaa4ccd-fc9b-cadd-a859-498fbb550a6e"
            ],
            "metadata": {},
            "worker": ""
        },
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "metadata": {}
    }
]

datamanager = [
    {
        "objective_key": "48cc5ce4-d352-b859-e202-adb0d639ee09",
        "description": {
            "hash": "8acac2e3b700de1e27ee00b8cc0b49a883476d4234015658cbff7a701332a498",
            "storage_address": "http://testserver/data_manager/e25a6ac0-b496-6c72-a339-45bdeb1f9f6f/description/"
        },
        "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
        "metadata": {},
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_global - Dataset 0",
        "opener": {
            "hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "storage_address": "http://testserver/data_manager/e25a6ac0-b496-6c72-a339-45bdeb1f9f6f/opener/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "type": "Test"
    },
    {
        "objective_key": "b61067adc59fb1aabe21eab767d986cccccdcfd8c64ea90a0bef59999051cea3",
        "description": {
            "hash": "0b32ac306997ff74a6b24e79264133de33d841e546f3f88b26a18d46e18223d9",
            "storage_address": "http://testserver/data_manager/aa572a96-4b02-4435-d48a-73aacb86e3d1/description/"
        },
        "key": "aa572a96-4b02-4435-d48a-73aacb86e3d1",
        "metadata": {},
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_global - Dataset 1",
        "opener": {
            "hash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
            "storage_address": "http://testserver/data_manager/aa572a96-4b02-4435-d48a-73aacb86e3d1/opener/"
        },
        "owner": "MyOrg2MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "type": "Test"
    }
]

algo = [
    {
        "key": "4942edc4-47b4-1439-1d00-47fb6379c2df",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple - Algo 0",
        "content": {
            "hash": "4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be",
            "storage_address": "http://testserver/algo/4942edc4-47b4-1439-1d00-47fb6379c2df/file/"
        },
        "description": {
            "hash": "22b9af671a660afd001b15c5a85edaa81dc42fbda7aef03f2fd76aa10d2e5151",
            "storage_address": "http://testserver/algo/4942edc4-47b4-1439-1d00-47fb6379c2df/description/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "metadata": {}
    },
    {
        "key": "59eb3834-97c3-37e2-80f2-d7c6805cb80b",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_federated_learning_workflow - Algo 0",
        "content": {
            "hash": "59eb383497c337e280f2d7c6805cb80bb623dfe581b6289eeee4fc62aefd9c30",
            "storage_address": "http://testserver/algo/59eb3834-97c3-37e2-80f2-d7c6805cb80b/file/"
        },
        "description": {
            "hash": "df548aab4b1a66e08021774e0b70e6f59b858ba41afa550396d213357326f891",
            "storage_address": "http://testserver/algo/59eb3834-97c3-37e2-80f2-d7c6805cb80b/description/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "metadata": {}
    },
    {
        "key": "e9481a81-278d-988f-3d7c-c8ba095b88f3",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_same_node - Algo 0",
        "content": {
            "hash": "e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8",
            "storage_address": "http://testserver/algo/e9481a81-278d-988f-3d7c-c8ba095b88f3/file/"
        },
        "description": {
            "hash": "851fc503e6136c86f4a0f4035aa6d59c44f017694757769b9b2d7d39a7f5dc3c",
            "storage_address": "http://testserver/algo/e9481a81-278d-988f-3d7c-c8ba095b88f3/description/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "metadata": {}
    },
    {
        "key": "ebbd8c65-dfe0-7d82-6d69-2f806deceffd",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_traintuple_execution_failure - Algo 0",
        "content": {
            "hash": "ebbd8c65dfe07d826d692f806deceffd296e715fa4db9e652304180dd7ee293d",
            "storage_address": "http://testserver/algo/ebbd8c65-dfe0-7d82-6d69-2f806deceffd/file/"
        },
        "description": {
            "hash": "d0289ce5f4ec35ea5eff7dc76b36cdc93c90bc3d76f55a8707a701f699742292",
            "storage_address": "http://testserver/algo/ebbd8c65-dfe0-7d82-6d69-2f806deceffd/description/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "metadata": {}
    },
    {
        "key": "c8efb021-f79c-5adc-96e9-ba8407c368a5",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_different_nodes - Algo 0",
        "content": {
            "hash": "c8efb021f79c5adc96e9ba8407c368a5a3e76f2b37164176059855cc9daae593",
            "storage_address": "http://testserver/algo/c8efb021-f79c-5adc-96e9-ba8407c368a5/file/"
        },
        "description": {
            "hash": "9a56aa11bdb75a1b5c2641493d546d4a28ec4d9d60aa0df18f5c2a019f8518b7",
            "storage_address": "http://testserver/algo/c8efb021-f79c-5adc-96e9-ba8407c368a5/description/"
        },
        "owner": "MyOrg2MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "metadata": {}
    }
]

traintuple = [
    {
        "key": "3169bb17-2502-f675-56a6-f12b856a5d65",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple - Algo 0",
            "hash": "4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be",
            "storage_address": "http://testserver/algo/4942edc4-47b4-1439-1d00-47fb6379c2df/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e26-3959-8c42-bbf9-aba8d223c6a5"
            ],
            "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "compute_plan_id": "",
        "in_models": None,
        "log": "",
        "metadata": {},
        "out_model": {
            "key": "940262c3-5a6b-33c2-b7c8-811fa785899b",
            "hash": "940262c35a6b33c2b7c8811fa785899b00e287ffa05e3cb5a23c857e9c89c760",
            "storage_address": "http://testserver/model/940262c35a6b33c2b7c8811fa785899b00e287ffa05e3cb5a23c857e9c89c760/file/"
        },
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "rank": 0,
        "status": "done",
        "tag": ""
    },
    {
        "key": "a9c586b7-2c9c-1141-2b0c-9f81d599651a",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple - Algo 0",
            "hash": "4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be",
            "storage_address": "http://testserver/algo/4942edc4-47b4-1439-1d00-47fb6379c2df/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "worker": "MyOrg1MSP",
            "keys": [
                "5702a4f5-61da-7827-35e2-e5d7b03605ee"
            ],
            "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "compute_plan_id": "",
        "in_models": None,
        "log": "",
        "metadata": {},
        "out_model": {
            "key": "f33d3c7a-21e9-7f5f-0edd-636f3b313c6a",
            "hash": "f33d3c7a21e97f5f0edd636f3b313c6a7757cc458614e49da74d58af7fc0c4c2",
            "storage_address": "http://testserver/model/f33d3c7a21e97f5f0edd636f3b313c6a7757cc458614e49da74d58af7fc0c4c2/file/"
        },
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "rank": 0,
        "status": "done",
        "tag": ""
    },
    {
        "key": "ea7180cc-c125-dcce-ff10-400fd2943f1e",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple - Algo 0",
            "hash": "4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be",
            "storage_address": "http://testserver/algo/4942edc4-47b4-1439-1d00-47fb6379c2df/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "worker": "MyOrg1MSP",
            "keys": [
                "51d906cc-10b2-9eb8-1c93-5550b7508119"
            ],
            "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "compute_plan_id": "",
        "in_models": None,
        "log": "",
        "metadata": {},
        "out_model": {
            "key": "02ccc4ee-b426-f7bb-fe74-6a06a4c63a20",
            "hash": "02ccc4eeb426f7bbfe746a06a4c63a2023a8f2ea2c72f92242cc5f7f1164383c",
            "storage_address": "http://testserver/model/02ccc4eeb426f7bbfe746a06a4c63a2023a8f2ea2c72f92242cc5f7f1164383c/file/"
        },
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "rank": 0,
        "status": "done",
        "tag": ""
    },
    {
        "key": "137804ca-8660-8780-62e4-19e340efd282",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_federated_learning_workflow - Algo 0",
            "hash": "59eb383497c337e280f2d7c6805cb80bb623dfe581b6289eeee4fc62aefd9c30",
            "storage_address": "http://testserver/algo/59eb3834-97c3-37e2-80f2-d7c6805cb80b/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg2MSP",
            "keys": [
                "26e52856-b272-61fc-12e9-615d5914027d",
                "70474091-7e35-b366-48b8-0d9826e1f24d",
                "88608067-e903-a7b5-cbfe-d480e7c4ee9e",
                "e453da42-246d-9be3-3204-fa30fb91755b"
            ],
            "opener_hash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
            "metadata": {}
        },
        "compute_plan_id": "4a7f743fd9a5ccaa6f8366a10f92955486ab15116a1e43f6c1ba1b9504f6b157",
        "in_models": [
            {
                "traintuple_key": "49dedc3b-4e76-3a2d-09e3-9f4e5eee3d49",
                "hash": "714ee81465576b09f1e4c6e0f28e82189501c46ed36569c9867eff851a285888",
                "storage_address": "http://testserver/model/714ee81465576b09f1e4c6e0f28e82189501c46ed36569c9867eff851a285888/file/"
            }
        ],
        "log": "",
        "metadata": {},
        "out_model": {
            "key": "4672cd5a-9e13-4a6f-6c54-144c3a8e8330",
            "hash": "4672cd5a9e134a6f6c54144c3a8e8330b2147fa10264ca8e9fbac9b9075cacd0",
            "storage_address": "http://backend-org-2-substra-backend-server.org-2:8000/model/4672cd5a9e134a6f6c54144c3a8e8330b2147fa10264ca8e9fbac9b9075cacd0/file/"
        },
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "rank": 1,
        "status": "done",
        "tag": "foo"
    },
    {
        "key": "49dedc3b-4e76-3a2d-09e3-9f4e5eee3d49",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_federated_learning_workflow - Algo 0",
            "hash": "59eb383497c337e280f2d7c6805cb80bb623dfe581b6289eeee4fc62aefd9c30",
            "storage_address": "http://testserver/algo/59eb3834-97c3-37e2-80f2-d7c6805cb80b/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e26-3959-8c42-bbf9-aba8d223c6a5",
                "51d906cc-10b2-9eb8-1c93-5550b7508119",
                "5702a4f5-61da-7827-35e2-e5d7b03605ee",
                "8524b404-cc1b-2531-4fce-92b8c31da7b1"
            ],
            "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "compute_plan_id": "4a7f743fd9a5ccaa6f8366a10f92955486ab15116a1e43f6c1ba1b9504f6b157",
        "in_models": None,
        "log": "",
        "metadata": {},
        "out_model": {
            "key": "714ee814-6557-6b09-f1e4-c6e0f28e8218",
            "hash": "714ee81465576b09f1e4c6e0f28e82189501c46ed36569c9867eff851a285888",
            "storage_address": "http://testserver/model/714ee81465576b09f1e4c6e0f28e82189501c46ed36569c9867eff851a285888/file/"
        },
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "rank": 0,
        "status": "done",
        "tag": "foo"
    },
    {
        "key": "e623fe67-c0dc-4ed7-8d4e-34f9f0fad0ac",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_different_nodes - Algo 0",
            "hash": "c8efb021f79c5adc96e9ba8407c368a5a3e76f2b37164176059855cc9daae593",
            "storage_address": "http://backend-org-2-substra-backend-server.org-2:8000/algo/c8efb021-f79c-5adc-96e9-ba8407c368a5/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg2MSP",
            "keys": [
                "26e52856-b272-61fc-12e9-615d5914027d",
                "70474091-7e35-b366-48b8-0d9826e1f24d",
                "88608067-e903-a7b5-cbfe-d480e7c4ee9e",
                "e453da42-246d-9be3-3204-fa30fb91755b"
            ],
            "opener_hash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
            "metadata": {}
        },
        "compute_plan_id": "",
        "in_models": None,
        "log": "",
        "metadata": {},
        "out_model": {
            "key": "d771446f-0be1-5eba-a66d-b902f5a98a50",
            "hash": "d771446f0be15ebaa66db902f5a98a5005611de4ea44d3a5fe77c50ee34ff114",
            "storage_address": "http://backend-org-2-substra-backend-server.org-2:8000/model/d771446f0be15ebaa66db902f5a98a5005611de4ea44d3a5fe77c50ee34ff114/file/"
        },
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "rank": 0,
        "status": "done",
        "tag": ""
    },
    {
        "key": "e3aab7fe-0c51-e970-edec-dfa1f780fd52",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_same_node - Algo 0",
            "hash": "e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8",
            "storage_address": "http://testserver/algo/e9481a81-278d-988f-3d7c-c8ba095b88f3/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e26-3959-8c42-bbf9-aba8d223c6a5",
                "51d906cc-10b2-9eb8-1c93-5550b7508119",
                "5702a4f5-61da-7827-35e2-e5d7b03605ee",
                "8524b404-cc1b-2531-4fce-92b8c31da7b1"
            ],
            "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "compute_plan_id": "",
        "in_models": None,
        "log": "",
        "metadata": {
            "foo": "bar"
        },
        "out_model": {
            "key": "420ce592-a42e-0c78-e644-447173b54046",
            "hash": "420ce592a42e0c78e644447173b54046163a2afeadd37227cef6866fc7d4c4f7",
            "storage_address": "http://testserver/model/420ce592a42e0c78e644447173b54046163a2afeadd37227cef6866fc7d4c4f7/file/"
        },
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "rank": 0,
        "status": "done",
        "tag": ""
    },
    {
        "key": "fcdbcf06-d54b-634e-dfe2-dd2d46cfe8d6",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_same_node - Algo 0",
            "hash": "e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8",
            "storage_address": "http://testserver/algo/e9481a81-278d-988f-3d7c-c8ba095b88f3/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e26-3959-8c42-bbf9-aba8d223c6a5",
                "51d906cc-10b2-9eb8-1c93-5550b7508119",
                "5702a4f5-61da-7827-35e2-e5d7b03605ee",
                "8524b404-cc1b-2531-4fce-92b8c31da7b1"
            ],
            "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "compute_plan_id": "",
        "in_models": [
            {
                "traintuple_key": "e3aab7fe-0c51-e970-edec-dfa1f780fd52",
                "hash": "420ce592a42e0c78e644447173b54046163a2afeadd37227cef6866fc7d4c4f7",
                "storage_address": "http://testserver/model/420ce592a42e0c78e644447173b54046163a2afeadd37227cef6866fc7d4c4f7/file/"
            }
        ],
        "log": "",
        "metadata": {},
        "out_model": {
            "key": "7b3183a9-9222-df2b-18de-11c8f767fdca",
            "hash": "7b3183a99222df2b18de11c8f767fdca2c7ebb0d4fa8bfe03c4f169cfea2aba2",
            "storage_address": "http://testserver/model/7b3183a99222df2b18de11c8f767fdca2c7ebb0d4fa8bfe03c4f169cfea2aba2/file/"
        },
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "rank": 0,
        "status": "done",
        "tag": ""
    },
    {
        "key": "5e18aef8-a674-8b22-0c82-532c39b29715",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_traintuple_execution_failure - Algo 0",
            "hash": "ebbd8c65dfe07d826d692f806deceffd296e715fa4db9e652304180dd7ee293d",
            "storage_address": "http://testserver/algo/ebbd8c65-dfe0-7d82-6d69-2f806deceffd/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e26-3959-8c42-bbf9-aba8d223c6a5",
                "51d906cc-10b2-9eb8-1c93-5550b7508119",
                "5702a4f5-61da-7827-35e2-e5d7b03605ee",
                "8524b404-cc1b-2531-4fce-92b8c31da7b1"
            ],
            "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "compute_plan_id": "",
        "in_models": None,
        "log": "[00-01-0117-d64af6f]",
        "metadata": {},
        "out_model": None,
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
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
            "storage_address": "http://testserver/composite_algo/09abcf99-a672-c0b9-5b3d-2431169e34ec/file/"
        },
        "certified": True,
        "compute_plan_id": "",
        "creator": "MyOrg1MSP",
        "dataset": {
            "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "worker": "MyOrg1MSP",
            "keys": [
                "ffed4147-ffff-f2f1-8130-b7332c1460ec"
            ],
            "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "perf": 32
        },
        "key": "8cd0eb9a-e234-9fc3-3b36-ebb689963840",
        "log": "",
        "metadata": {},
        "objective": {
            "key": "48cc5ce4-d352-b859-e202-adb0d639ee09",
            "metrics": {
                "hash": "0d64f855e07524da60203067713ab08fd6e479a02ebcb70364b2c6a2a29367e1",
                "storage_address": "http://testserver/objective/48cc5ce4-d352-b859-e202-adb0d639ee09/metrics/"
            }
        },
        "rank": 0,
        "status": "done",
        "tag": "bar",
        "traintuple_key": "2978ca1f-7d55-20ef-42a8-2c86a2e24d5b",
        "traintuple_type": "composite_traintuple"
    },
    {
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
            "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
            "storage_address": "http://testserver/composite_algo/fe2eba45-66fa-c967-ef84-7cbb3a8eba75/file/"
        },
        "certified": True,
        "compute_plan_id": "",
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg2MSP",
            "keys": [
                "edaa4ccd-fc9b-cadd-a859-498fbb550a6e"
            ],
            "opener_hash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
            "perf": 32
        },
        "key": "87e83565-0d84-ca0c-f26a-c332bad4f4d7",
        "log": "",
        "metadata": {},
        "objective": {
            "key": "b61067ad-c59f-b1aa-be21-eab767d986cc",
            "metrics": {
                "hash": "1a61bea02e3e75f8197d682cbaa6110c9709fbfbd4f16964acc390c70e7a22fe",
                "storage_address": "http://backend-org-2-substra-backend-server.org-2:8000/objective/b61067ad-c59f-b1aa-be21-eab767d986cc/metrics/"
            }
        },
        "rank": 0,
        "status": "done",
        "tag": "",
        "traintuple_key": "3be92d96-d1ab-dabf-be6a-4ff612d70f7f",
        "traintuple_type": "composite_traintuple"
    },
    {
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
            "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
            "storage_address": "http://testserver/composite_algo/fe2eba45-66fa-c967-ef84-7cbb3a8eba75/file/"
        },
        "certified": True,
        "compute_plan_id": "",
        "creator": "MyOrg1MSP",
        "dataset": {
            "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "worker": "MyOrg1MSP",
            "keys": [
                "ffed4147-ffff-f2f1-8130-b7332c1460ec"
            ],
            "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "perf": 32
        },
        "key": "6075c796-cc47-0f1e-1de7-b98d8a4d28b1",
        "log": "",
        "metadata": {},
        "objective": {
            "key": "48cc5ce4-d352-b859-e202-adb0d639ee09",
            "metrics": {
                "hash": "0d64f855e07524da60203067713ab08fd6e479a02ebcb70364b2c6a2a29367e1",
                "storage_address": "http://testserver/objective/48cc5ce4-d352-b859-e202-adb0d639ee09/metrics/"
            }
        },
        "rank": 0,
        "status": "done",
        "tag": "",
        "traintuple_key": "5adbd24e-a21c-b23b-1ffc-65151038a62c",
        "traintuple_type": "composite_traintuple"
    },
    {
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_same_node - Algo 0",
            "hash": "e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8",
            "storage_address": "http://testserver/algo/e9481a81-278d-988f-3d7c-c8ba095b88f3/file/"
        },
        "certified": True,
        "compute_plan_id": "",
        "creator": "MyOrg1MSP",
        "dataset": {
            "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "worker": "MyOrg1MSP",
            "keys": [
                "ffed4147-ffff-f2f1-8130-b7332c1460ec"
            ],
            "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "perf": 2
        },
        "key": "e2f386a8-8a17-02ce-cf02-70742a31cdf0",
        "log": "",
        "metadata": {},
        "objective": {
            "key": "48cc5ce4-d352-b859-e202-adb0d639ee09",
            "metrics": {
                "hash": "0d64f855e07524da60203067713ab08fd6e479a02ebcb70364b2c6a2a29367e1",
                "storage_address": "http://testserver/objective/48cc5ce4-d352-b859-e202-adb0d639ee09/metrics/"
            }
        },
        "rank": 0,
        "status": "done",
        "tag": "",
        "traintuple_key": "e3aab7fe-0c51-e970-edec-dfa1f780fd52",
        "traintuple_type": "traintuple"
    },
    {
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_different_nodes - Algo 0",
            "hash": "c8efb021f79c5adc96e9ba8407c368a5a3e76f2b37164176059855cc9daae593",
            "storage_address": "http://backend-org-2-substra-backend-server.org-2:8000/algo/c8efb021-f79c-5adc-96e9-ba8407c368a5/file/"
        },
        "certified": True,
        "compute_plan_id": "",
        "creator": "MyOrg1MSP",
        "dataset": {
            "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "worker": "MyOrg1MSP",
            "keys": [
                "ffed4147-ffff-f2f1-8130-b7332c1460ec"
            ],
            "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "perf": 2
        },
        "key": "05996970-85f3-43a8-298e-e3a87bd00002",
        "log": "",
        "metadata": {},
        "objective": {
            "key": "48cc5ce4-d352-b859-e202-adb0d639ee09",
            "metrics": {
                "hash": "0d64f855e07524da60203067713ab08fd6e479a02ebcb70364b2c6a2a29367e1",
                "storage_address": "http://testserver/objective/48cc5ce4-d352-b859-e202-adb0d639ee09/metrics/"
            }
        },
        "rank": 0,
        "status": "done",
        "tag": "",
        "traintuple_key": "e623fe67-c0dc-4ed7-8d4e-34f9f0fad0ac",
        "traintuple_type": "traintuple"
    }
]

computeplan = [
    {
        "compute_plan_id": "4a7f743f-d9a5-ccaa-6f83-66a10f929554",
        "traintuple_keys": [
            "49dedc3b-4e76-3a2d-09e3-9f4e5eee3d49",
            "137804ca-8660-8780-62e4-19e340efd282"
        ],
        "aggregatetuple_keys": None,
        "composite_traintuple_keys": None,
        "testtuple_keys": None,
        "clean_models": False,
        "tag": "",
        "metadata": {},
        "status": "done",
        "tuple_count": 2,
        "done_count": 2,
        "id_to_key": {}
    }
]

compositetraintuple = [
    {
        "key": "2978ca1f-7d55-20ef-42a8-2c86a2e24d5b",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuples_execution - Algo 0",
            "hash": "09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf",
            "storage_address": "http://testserver/composite_algo/09abcf99-a672-c0b9-5b3d-2431169e34ec/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e26-3959-8c42-bbf9-aba8d223c6a5",
                "51d906cc-10b2-9eb8-1c93-5550b7508119",
                "5702a4f5-61da-7827-35e2-e5d7b03605ee",
                "8524b404-cc1b-2531-4fce-92b8c31da7b1"
            ],
            "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "compute_plan_id": "",
        "in_head_model": {
            "traintuple_key": "aa9be143-edc6-ef05-1ea2-55fd77bb54ba",
            "hash": "64c72dc39772e122ef552d10ff101ef6cee94935a84678a0125f7c3fd044dff8",
            "storage_address": ""
        },
        "in_trunk_model": {
            "traintuple_key": "aa9be143-edc6-ef05-1ea2-55fd77bb54ba",
            "hash": "00009a1256f8ce55ed907221000035daf1ac28111b5a3a03289da2f0601edf8f",
            "storage_address": "http://testserver/model/00009a1256f8ce55ed907221000035daf1ac28111b5a3a03289da2f0601edf8f/file/"
        },
        "log": "",
        "metadata": {},
        "out_head_model": {
            "out_model": {
                "hash": "349b475ebd9458739af8685b8b75d7aeb1290209eabadad1b9b8afaa2b05c8d5"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "out_trunk_model": {
            "out_model": {
                "key": "692e3f70-b9eb-fca3-c2e5-1e2a92c18092",
                "hash": "692e3f70b9ebfca3c2e51e2a92c18092cc24dda547debefd6eb4bdd38ca6d803",
                "storage_address": "http://testserver/model/692e3f70b9ebfca3c2e51e2a92c18092cc24dda547debefd6eb4bdd38ca6d803/file/"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
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
        "key": "aa9be143-edc6-ef05-1ea2-55fd77bb54ba",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuples_execution - Algo 0",
            "hash": "09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf",
            "storage_address": "http://testserver/composite_algo/09abcf99-a672-c0b9-5b3d-2431169e34ec/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e26-3959-8c42-bbf9-aba8d223c6a5",
                "51d906cc-10b2-9eb8-1c93-5550b7508119",
                "5702a4f5-61da-7827-35e2-e5d7b03605ee",
                "8524b404-cc1b-2531-4fce-92b8c31da7b1"
            ],
            "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "compute_plan_id": "",
        "in_head_model": None,
        "in_trunk_model": None,
        "log": "",
        "metadata": {},
        "out_head_model": {
            "out_model": {
                "hash": "64c72dc39772e122ef552d10ff101ef6cee94935a84678a0125f7c3fd044dff8"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "out_trunk_model": {
            "out_model": {
                "key": "00009a12-56f8-ce55-ed90-7221000035da",
                "hash": "00009a1256f8ce55ed907221000035daf1ac28111b5a3a03289da2f0601edf8f",
                "storage_address": "http://testserver/model/00009a1256f8ce55ed907221000035daf1ac28111b5a3a03289da2f0601edf8f/file/"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
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
        "key": "2d3e98fb-eafe-bf19-95db-3ab205b9f803",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuple_execution_failure - Algo 0",
            "hash": "0fbb505a32ae8785c08d37fe7bf7476d7365c3a0cef7c6e05c61c06db3267593",
            "storage_address": "http://testserver/composite_algo/0fbb505a-32ae-8785-c08d-37fe7bf7476d/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e26-3959-8c42-bbf9-aba8d223c6a5",
                "51d906cc-10b2-9eb8-1c93-5550b7508119",
                "5702a4f5-61da-7827-35e2-e5d7b03605ee",
                "8524b404-cc1b-2531-4fce-92b8c31da7b1"
            ],
            "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "compute_plan_id": "",
        "in_head_model": None,
        "in_trunk_model": None,
        "log": "[00-01-0117-d390d32]",
        "metadata": {},
        "out_head_model": {
            "out_model": None,
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "out_trunk_model": {
            "out_model": None,
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
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
        "key": "7dbd4b2a-c9e8-1b6d-edd7-75809e0903d8",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple_execution_failure - Algo 0",
            "hash": "5a9fc1032bd97c9ebaafeaf7d2e5d81f375f1ff8e13ad3000e43f135eb47810c",
            "storage_address": "http://testserver/composite_algo/5a9fc103-2bd9-7c9e-baaf-eaf7d2e5d81f/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e26-3959-8c42-bbf9-aba8d223c6a5"
            ],
            "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "compute_plan_id": "",
        "in_head_model": None,
        "in_trunk_model": None,
        "log": "",
        "metadata": {},
        "out_head_model": {
            "out_model": {
                "hash": "8b87222907027a470d6d99409b0de9a9ced07142d026ab875d6ddfdecf9db96d"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "out_trunk_model": {
            "out_model": {
                "key": "fcfcaa4f-3be7-3940-006f-c54566b2946f",
                "hash": "fcfcaa4f3be73940006fc54566b2946fabd5ee677496a5dd43e4b8c0c3c3d54d",
                "storage_address": "http://testserver/model/fcfcaa4f3be73940006fc54566b2946fabd5ee677496a5dd43e4b8c0c3c3d54d/file/"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
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
        "key": "df3e1942-6496-a5b8-a79d-8f1b96e52de9",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple_execution_failure - Algo 0",
            "hash": "5a9fc1032bd97c9ebaafeaf7d2e5d81f375f1ff8e13ad3000e43f135eb47810c",
            "storage_address": "http://testserver/composite_algo/5a9fc103-2bd9-7c9e-baaf-eaf7d2e5d81f/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "worker": "MyOrg1MSP",
            "keys": [
                "51d906cc-10b2-9eb8-1c93-5550b7508119"
            ],
            "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "compute_plan_id": "",
        "in_head_model": None,
        "in_trunk_model": None,
        "log": "",
        "metadata": {},
        "out_head_model": {
            "out_model": {
                "hash": "bffb89749a253de1d451a836748dc813035dbcacb01fb85911b97c577c10ea6d"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "out_trunk_model": {
            "out_model": {
                "key": "682d31d9-e956-54ed-0aaf-81184136d87c",
                "hash": "682d31d9e95654ed0aaf81184136d87c7ff2a0046c3d24181508f112d58b330d",
                "storage_address": "http://testserver/model/682d31d9e95654ed0aaf81184136d87c7ff2a0046c3d24181508f112d58b330d/file/"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
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
        "key": "3197bd6c-56bc-4708-9864-c76b47b6115e",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
            "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
            "storage_address": "http://testserver/composite_algo/fe2eba45-66fa-c967-ef84-7cbb3a8eba75/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "worker": "MyOrg1MSP",
            "keys": [
                "265f1e26-3959-8c42-bbf9-aba8d223c6a5"
            ],
            "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "compute_plan_id": "",
        "in_head_model": None,
        "in_trunk_model": None,
        "log": "",
        "metadata": {},
        "out_head_model": {
            "out_model": {
                "hash": "7d7ed2eac5e822ea90058387dd35d1270639ecc4982a6d72b619b8659813163a"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "out_trunk_model": {
            "out_model": {
                "key": "b312a262-592a-a7ed-56a0-7d0eb02bec05",
                "hash": "b312a262592aa7ed56a07d0eb02bec0548745eb7316d4ea86b3719b2497d8cb2",
                "storage_address": "http://testserver/model/b312a262592aa7ed56a07d0eb02bec0548745eb7316d4ea86b3719b2497d8cb2/file/"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
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
        "key": "3be92d96-d1ab-dabf-be6a-4ff612d70f7f",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
            "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
            "storage_address": "http://testserver/composite_algo/fe2eba45-66fa-c967-ef84-7cbb3a8eba75/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg2MSP",
            "keys": [
                "70474091-7e35-b366-48b8-0d9826e1f24d"
            ],
            "opener_hash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
            "metadata": {}
        },
        "compute_plan_id": "",
        "in_head_model": {
            "traintuple_key": "e7b96818-eadc-dce6-940c-16b388bbd264",
            "hash": "3af8f86ed9fe07237497e52d1ced195d7e4752f7d130327929f96ea688d60a41",
            "storage_address": ""
        },
        "in_trunk_model": {
            "traintuple_key": "9cb5582f-c3e8-22b9-ddab-bf7479097df0",
            "hash": "4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688",
            "storage_address": "http://testserver/model/4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688/file/"
        },
        "log": "",
        "metadata": {},
        "out_head_model": {
            "out_model": {
                "hash": "8b6a7f3b7feef0a2c157bf2acfd2596fd7815a0a69b0a41b7451bab47d022eaa"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
                        "MyOrg2MSP"
                    ]
                }
            }
        },
        "out_trunk_model": {
            "out_model": {
                "key": "66392ca3-e6a5-935f-b8e2-2a5ee5b8af31",
                "hash": "66392ca3e6a5935fb8e22a5ee5b8af31dbec5655ff087b98f071abf7e4f3ce74",
                "storage_address": "http://backend-org-2-substra-backend-server.org-2:8000/model/66392ca3e6a5935fb8e22a5ee5b8af31dbec5655ff087b98f071abf7e4f3ce74/file/"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
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
        "key": "5adbd24e-a21c-b23b-1ffc-65151038a62c",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
            "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
            "storage_address": "http://testserver/composite_algo/fe2eba45-66fa-c967-ef84-7cbb3a8eba75/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
            "worker": "MyOrg1MSP",
            "keys": [
                "51d906cc-10b2-9eb8-1c93-5550b7508119"
            ],
            "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
            "metadata": {}
        },
        "compute_plan_id": "",
        "in_head_model": {
            "traintuple_key": "3197bd6c-56bc-4708-9864-c76b47b6115e",
            "hash": "7d7ed2eac5e822ea90058387dd35d1270639ecc4982a6d72b619b8659813163a",
            "storage_address": ""
        },
        "in_trunk_model": {
            "traintuple_key": "9cb5582f-c3e8-22b9-ddab-bf7479097df0",
            "hash": "4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688",
            "storage_address": "http://testserver/model/4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688/file/"
        },
        "log": "",
        "metadata": {},
        "out_head_model": {
            "out_model": {
                "hash": "28a705e08e765569bd89262f821e1c7285e43fa1e82df2f833464b8ff890c7bd"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
                        "MyOrg1MSP"
                    ]
                }
            }
        },
        "out_trunk_model": {
            "out_model": {
                "key": "14b7e325-4896-db4f-43c5-82695c39d096",
                "hash": "14b7e3254896db4f43c582695c39d096f33e1390e3ecaa8b0e6e7619bf827044",
                "storage_address": "http://testserver/model/14b7e3254896db4f43c582695c39d096f33e1390e3ecaa8b0e6e7619bf827044/file/"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
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
        "key": "e7b96818-eadc-dce6-940c-16b388bbd264",
        "algo": {
            "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
            "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
            "storage_address": "http://testserver/composite_algo/fe2eba45-66fa-c967-ef84-7cbb3a8eba75/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg2MSP",
            "keys": [
                "26e52856-b272-61fc-12e9-615d5914027d"
            ],
            "opener_hash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
            "metadata": {}
        },
        "compute_plan_id": "",
        "in_head_model": None,
        "in_trunk_model": None,
        "log": "",
        "metadata": {},
        "out_head_model": {
            "out_model": {
                "hash": "3af8f86ed9fe07237497e52d1ced195d7e4752f7d130327929f96ea688d60a41"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
                        "MyOrg2MSP"
                    ]
                }
            }
        },
        "out_trunk_model": {
            "out_model": {
                "key": "cd8a895a-9b60-4ccb-b2e2-bf9f081d0560",
                "hash": "cd8a895a9b604ccbb2e2bf9f081d0560bfd86f4a98beabd833d4c7c36f35cd9d",
                "storage_address": "http://backend-org-2-substra-backend-server.org-2:8000/model/cd8a895a9b604ccbb2e2bf9f081d0560bfd86f4a98beabd833d4c7c36f35cd9d/file/"
            },
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
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
        "key": "09abcf99-a672-c0b9-5b3d-2431169e34ec",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuples_execution - Algo 0",
        "content": {
            "hash": "09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf",
            "storage_address": "http://testserver/composite_algo/09abcf99-a672-c0b9-5b3d-2431169e34ec/file/"
        },
        "description": {
            "hash": "aa444b9dc8cac0c80263b3970ddc403757abc6bcb546eb322a1711f1b8ec294d",
            "storage_address": "http://testserver/composite_algo/09abcf99-a672-c0b9-5b3d-2431169e34ec/description/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "metadata": {}
    },
    {
        "key": "0fbb505a-32ae-8785-c08d-37fe7bf7476d",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuple_execution_failure - Algo 0",
        "content": {
            "hash": "0fbb505a32ae8785c08d37fe7bf7476d7365c3a0cef7c6e05c61c06db3267593",
            "storage_address": "http://testserver/composite_algo/0fbb505a-32ae-8785-c08d-37fe7bf7476d/file/"
        },
        "description": {
            "hash": "6d184a2e6d8097cc55e4b435bbd5b9c6d7211274472585448411cd435149e941",
            "storage_address": "http://testserver/composite_algo/0fbb505a-32ae-8785-c08d-37fe7bf7476d/description/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "metadata": {}
    },
    {
        "key": "5a9fc103-2bd9-7c9e-baaf-eaf7d2e5d81f",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple_execution_failure - Algo 0",
        "content": {
            "hash": "5a9fc1032bd97c9ebaafeaf7d2e5d81f375f1ff8e13ad3000e43f135eb47810c",
            "storage_address": "http://testserver/composite_algo/5a9fc103-2bd9-7c9e-baaf-eaf7d2e5d81f/file/"
        },
        "description": {
            "hash": "61cc1c0f3962bc4d60151041e02b55ca9788ea7a8a848dfc67f3fc3194b5a202",
            "storage_address": "http://testserver/composite_algo/5a9fc103-2bd9-7c9e-baaf-eaf7d2e5d81f/description/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "metadata": {}
    },
    {
        "key": "fe2eba45-66fa-c967-ef84-7cbb3a8eba75",
        "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
        "content": {
            "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
            "storage_address": "http://testserver/composite_algo/fe2eba45-66fa-c967-ef84-7cbb3a8eba75/file/"
        },
        "description": {
            "hash": "066d354d20dfa689cd5ca22f99445dc47589971c6d958bd6841beeae585f1054",
            "storage_address": "http://testserver/composite_algo/fe2eba45-66fa-c967-ef84-7cbb3a8eba75/description/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorized_ids": []
            }
        },
        "metadata": {}
    }
]

model = [
    {
        "traintuple": {
            "key": "3169bb17-2502-f675-56a6-f12b856a5d65",
            "algo": {
                "key": "4942edc4-47b4-1439-1d00-47fb6379c2df",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple - Algo 0",
                "hash": "4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be",
                "storage_address": "http://testserver/algo/4942edc4-47b4-1439-1d00-47fb6379c2df/file/"
            },
            "creator": "MyOrg1MSP",
        "dataset": {
                "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e26-3959-8c42-bbf9-aba8d223c6a5"
                ],
                "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "compute_plan_id": "",
            "in_models": None,
            "log": "",
            "metadata": {},
            "out_model": {
                "key": "940262c3-5a6b-33c2-b7c8-811fa785899b",
                "hash": "940262c35a6b33c2b7c8811fa785899b00e287ffa05e3cb5a23c857e9c89c760",
                "storage_address": "http://testserver/model/940262c35a6b33c2b7c8811fa785899b00e287ffa05e3cb5a23c857e9c89c760/file/"
            },
            "permissions": {
                "process": {
                    "public": True,
                    "authorized_ids": []
                }
            },
            "rank": 0,
            "status": "done",
            "tag": ""
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "compute_plan_id": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintuple_key": "",
            "traintuple_type": ""
        },
        "non_certified_testtuples": None
    },
    {
        "traintuple": {
            "key": "a9c586b7-2c9c-1141-2b0c-9f81d599651a",
            "algo": {
                "key": "4942edc4-47b4-1439-1d00-47fb6379c2df",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple - Algo 0",
                "hash": "4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be",
                "storage_address": "http://testserver/algo/4942edc4-47b4-1439-1d00-47fb6379c2df/file/"
            },
            "creator": "MyOrg1MSP",
        "dataset": {
                "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
                "worker": "MyOrg1MSP",
                "keys": [
                    "5702a4f5-61da-7827-35e2-e5d7b03605ee"
                ],
                "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "compute_plan_id": "",
            "in_models": None,
            "log": "",
            "metadata": {},
            "out_model": {
                "key": "f33d3c7a-21e9-7f5f-0edd-636f3b313c6a",
                "hash": "f33d3c7a21e97f5f0edd636f3b313c6a7757cc458614e49da74d58af7fc0c4c2",
                "storage_address": "http://testserver/model/f33d3c7a21e97f5f0edd636f3b313c6a7757cc458614e49da74d58af7fc0c4c2/file/"
            },
            "permissions": {
                "process": {
                    "public": True,
                    "authorized_ids": []
                }
            },
            "rank": 0,
            "status": "done",
            "tag": ""
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "compute_plan_id": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintuple_key": "",
            "traintuple_type": ""
        },
        "non_certified_testtuples": None
    },
    {
        "traintuple": {
            "key": "ea7180cc-c125-dcce-ff10-400fd2943f1e",
            "algo": {
                "key": "4942edc4-47b4-1439-1d00-47fb6379c2df",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple - Algo 0",
                "hash": "4942edc447b414391d0047fb6379c2dfbcd96a68bbe3071c756dc4c2b2c951be",
                "storage_address": "http://testserver/algo/4942edc4-47b4-1439-1d00-47fb6379c2df/file/"
            },
            "creator": "MyOrg1MSP",
        "dataset": {
                "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
                "worker": "MyOrg1MSP",
                "keys": [
                    "51d906cc-10b2-9eb8-1c93-5550b7508119"
                ],
                "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "compute_plan_id": "",
            "in_models": None,
            "log": "",
            "metadata": {},
            "out_model": {
                "key": "02ccc4ee-b426-f7bb-fe74-6a06a4c63a20",
                "hash": "02ccc4eeb426f7bbfe746a06a4c63a2023a8f2ea2c72f92242cc5f7f1164383c",
                "storage_address": "http://testserver/model/02ccc4eeb426f7bbfe746a06a4c63a2023a8f2ea2c72f92242cc5f7f1164383c/file/"
            },
            "permissions": {
                "process": {
                    "public": True,
                    "authorized_ids": []
                }
            },
            "rank": 0,
            "status": "done",
            "tag": ""
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "compute_plan_id": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintuple_key": "",
            "traintuple_type": ""
        },
        "non_certified_testtuples": None
    },
    {
        "traintuple": {
            "key": "137804ca-8660-8780-62e4-19e340efd282",
            "algo": {
                "key": "59eb3834-97c3-37e2-80f2-d7c6805cb80b",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_federated_learning_workflow - Algo 0",
                "hash": "59eb383497c337e280f2d7c6805cb80bb623dfe581b6289eeee4fc62aefd9c30",
                "storage_address": "http://testserver/algo/59eb3834-97c3-37e2-80f2-d7c6805cb80b/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg2MSP",
                "keys": [
                    "26e52856-b272-61fc-12e9-615d5914027d",
                    "70474091-7e35-b366-48b8-0d9826e1f24d",
                    "88608067-e903-a7b5-cbfe-d480e7c4ee9e",
                    "e453da42-246d-9be3-3204-fa30fb91755b"
                ],
                "opener_hash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
                "metadata": {}
            },
            "compute_plan_id": "4a7f743fd9a5ccaa6f8366a10f92955486ab15116a1e43f6c1ba1b9504f6b157",
            "in_models": [
                {
                    "traintuple_key": "49dedc3b-4e76-3a2d-09e3-9f4e5eee3d49",
                    "hash": "714ee81465576b09f1e4c6e0f28e82189501c46ed36569c9867eff851a285888",
                    "storage_address": "http://testserver/model/714ee81465576b09f1e4c6e0f28e82189501c46ed36569c9867eff851a285888/file/"
                }
            ],
            "log": "",
            "metadata": {},
            "out_model": {
                "key": "4672cd5a-9e13-4a6f-6c54-144c3a8e8330",
                "hash": "4672cd5a9e134a6f6c54144c3a8e8330b2147fa10264ca8e9fbac9b9075cacd0",
                "storage_address": "http://backend-org-2-substra-backend-server.org-2:8000/model/4672cd5a9e134a6f6c54144c3a8e8330b2147fa10264ca8e9fbac9b9075cacd0/file/"
            },
            "permissions": {
                "process": {
                    "public": True,
                    "authorized_ids": []
                }
            },
            "rank": 1,
            "status": "done",
            "tag": "foo"
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "compute_plan_id": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintuple_key": "",
            "traintuple_type": ""
        },
        "non_certified_testtuples": None
    },
    {
        "traintuple": {
            "key": "49dedc3b-4e76-3a2d-09e3-9f4e5eee3d49",
            "algo": {
                "key": "59eb3834-97c3-37e2-80f2-d7c6805cb80b",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_federated_learning_workflow - Algo 0",
                "hash": "59eb383497c337e280f2d7c6805cb80bb623dfe581b6289eeee4fc62aefd9c30",
                "storage_address": "http://testserver/algo/59eb3834-97c3-37e2-80f2-d7c6805cb80b/file/"
            },
            "creator": "MyOrg1MSP",
        "dataset": {
                "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e26-3959-8c42-bbf9-aba8d223c6a5",
                    "51d906cc-10b2-9eb8-1c93-5550b7508119",
                    "5702a4f5-61da-7827-35e2-e5d7b03605ee",
                    "8524b404-cc1b-2531-4fce-92b8c31da7b1"
                ],
                "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "compute_plan_id": "4a7f743fd9a5ccaa6f8366a10f92955486ab15116a1e43f6c1ba1b9504f6b157",
            "in_models": None,
            "log": "",
            "metadata": {},
            "out_model": {
                "key": "714ee814-6557-6b09-f1e4-c6e0f28e8218",
                "hash": "714ee81465576b09f1e4c6e0f28e82189501c46ed36569c9867eff851a285888",
                "storage_address": "http://testserver/model/714ee81465576b09f1e4c6e0f28e82189501c46ed36569c9867eff851a285888/file/"
            },
            "permissions": {
                "process": {
                    "public": True,
                    "authorized_ids": []
                }
            },
            "rank": 0,
            "status": "done",
            "tag": "foo"
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "compute_plan_id": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintuple_key": "",
            "traintuple_type": ""
        },
        "non_certified_testtuples": None
    },
    {
        "traintuple": {
            "key": "e623fe67-c0dc-4ed7-8d4e-34f9f0fad0ac",
            "algo": {
                "key": "c8efb021-f79c-5adc-96e9-ba8407c368a5",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_different_nodes - Algo 0",
                "hash": "c8efb021f79c5adc96e9ba8407c368a5a3e76f2b37164176059855cc9daae593",
                "storage_address": "http://backend-org-2-substra-backend-server.org-2:8000/algo/c8efb021-f79c-5adc-96e9-ba8407c368a5/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg2MSP",
                "keys": [
                    "26e52856-b272-61fc-12e9-615d5914027d",
                    "70474091-7e35-b366-48b8-0d9826e1f24d",
                    "88608067-e903-a7b5-cbfe-d480e7c4ee9e",
                    "e453da42-246d-9be3-3204-fa30fb91755b"
                ],
                "opener_hash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
                "metadata": {}
            },
            "compute_plan_id": "",
            "in_models": None,
            "log": "",
            "metadata": {},
            "out_model": {
                "key": "d771446f-0be1-5eba-a66d-b902f5a98a50",
                "hash": "d771446f0be15ebaa66db902f5a98a5005611de4ea44d3a5fe77c50ee34ff114",
                "storage_address": "http://backend-org-2-substra-backend-server.org-2:8000/model/d771446f0be15ebaa66db902f5a98a5005611de4ea44d3a5fe77c50ee34ff114/file/"
            },
            "permissions": {
                "process": {
                    "public": True,
                    "authorized_ids": []
                }
            },
            "rank": 0,
            "status": "done",
            "tag": ""
        },
        "testtuple": {
            "algo": {
                "key": "c8efb021-f79c-5adc-96e9-ba8407c368a5",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_different_nodes - Algo 0",
                "hash": "c8efb021f79c5adc96e9ba8407c368a5a3e76f2b37164176059855cc9daae593",
                "storage_address": "http://backend-org-2-substra-backend-server.org-2:8000/algo/c8efb021-f79c-5adc-96e9-ba8407c368a5/file/"
            },
            "certified": True,
            "compute_plan_id": "",
            "creator": "MyOrg1MSP",
        "dataset": {
                "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
                "worker": "MyOrg1MSP",
                "keys": [
                    "ffed4147-ffff-f2f1-8130-b7332c1460ec"
                ],
                "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "perf": 2
            },
            "key": "05996970-85f3-43a8-298e-e3a87bd00002",
            "log": "",
            "metadata": {},
            "objective": {
                "key": "48cc5ce4-d352-b859-e202-adb0d639ee09",
                "metrics": {
                    "hash": "0d64f855e07524da60203067713ab08fd6e479a02ebcb70364b2c6a2a29367e1",
                    "storage_address": "http://testserver/objective/48cc5ce4-d352-b859-e202-adb0d639ee09/metrics/"
                }
            },
            "rank": 0,
            "status": "done",
            "tag": "",
            "traintuple_key": "e623fe67-c0dc-4ed7-8d4e-34f9f0fad0ac",
            "traintuple_type": "traintuple"
        },
        "non_certified_testtuples": None
    },
    {
        "traintuple": {
            "key": "e3aab7fe-0c51-e970-edec-dfa1f780fd52",
            "algo": {
                "key": "e9481a81-278d-988f-3d7c-c8ba095b88f3",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_same_node - Algo 0",
                "hash": "e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8",
                "storage_address": "http://testserver/algo/e9481a81-278d-988f-3d7c-c8ba095b88f3/file/"
            },
            "creator": "MyOrg1MSP",
        "dataset": {
                "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e26-3959-8c42-bbf9-aba8d223c6a5",
                    "51d906cc-10b2-9eb8-1c93-5550b7508119",
                    "5702a4f5-61da-7827-35e2-e5d7b03605ee",
                    "8524b404-cc1b-2531-4fce-92b8c31da7b1"
                ],
                "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "compute_plan_id": "",
            "in_models": None,
            "log": "",
            "metadata": {
                "foo": "bar"
            },
            "out_model": {
                "key": "420ce592-a42e-0c78-e644-447173b54046",
                "hash": "420ce592a42e0c78e644447173b54046163a2afeadd37227cef6866fc7d4c4f7",
                "storage_address": "http://testserver/model/420ce592a42e0c78e644447173b54046163a2afeadd37227cef6866fc7d4c4f7/file/"
            },
            "permissions": {
                "process": {
                    "public": True,
                    "authorized_ids": []
                }
            },
            "rank": 0,
            "status": "done",
            "tag": ""
        },
        "testtuple": {
            "algo": {
                "key": "e9481a81-278d-988f-3d7c-c8ba095b88f3",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_same_node - Algo 0",
                "hash": "e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8",
                "storage_address": "http://testserver/algo/e9481a81-278d-988f-3d7c-c8ba095b88f3/file/"
            },
            "certified": True,
            "compute_plan_id": "",
            "creator": "MyOrg1MSP",
        "dataset": {
                "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
                "worker": "MyOrg1MSP",
                "keys": [
                    "ffed4147-ffff-f2f1-8130-b7332c1460ec"
                ],
                "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "perf": 2
            },
            "key": "e2f386a8-8a17-02ce-cf02-70742a31cdf0",
            "log": "",
            "metadata": {},
            "objective": {
                "key": "48cc5ce4-d352-b859-e202-adb0d639ee09",
                "metrics": {
                    "hash": "0d64f855e07524da60203067713ab08fd6e479a02ebcb70364b2c6a2a29367e1",
                    "storage_address": "http://testserver/objective/48cc5ce4-d352-b859-e202-adb0d639ee09/metrics/"
                }
            },
            "rank": 0,
            "status": "done",
            "tag": "",
            "traintuple_key": "e3aab7fe-0c51-e970-edec-dfa1f780fd52",
            "traintuple_type": "traintuple"
        },
        "non_certified_testtuples": None
    },
    {
        "traintuple": {
            "key": "fcdbcf06-d54b-634e-dfe2-dd2d46cfe8d6",
            "algo": {
                "key": "e9481a81-278d-988f-3d7c-c8ba095b88f3",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_tuples_execution_on_same_node - Algo 0",
                "hash": "e9481a81278d988f3d7cc8ba095b88f33d7cc0da3f0c0a30ca942ba34f235ff8",
                "storage_address": "http://testserver/algo/e9481a81-278d-988f-3d7c-c8ba095b88f3/file/"
            },
            "creator": "MyOrg1MSP",
        "dataset": {
                "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e26-3959-8c42-bbf9-aba8d223c6a5",
                    "51d906cc-10b2-9eb8-1c93-5550b7508119",
                    "5702a4f5-61da-7827-35e2-e5d7b03605ee",
                    "8524b404-cc1b-2531-4fce-92b8c31da7b1"
                ],
                "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "compute_plan_id": "",
            "in_models": [
                {
                    "traintuple_key": "e3aab7fe-0c51-e970-edec-dfa1f780fd52",
                    "hash": "420ce592a42e0c78e644447173b54046163a2afeadd37227cef6866fc7d4c4f7",
                    "storage_address": "http://testserver/model/420ce592a42e0c78e644447173b54046163a2afeadd37227cef6866fc7d4c4f7/file/"
                }
            ],
            "log": "",
            "metadata": {},
            "out_model": {
                "key": "7b3183a9-9222-df2b-18de-11c8f767fdca",
                "hash": "7b3183a99222df2b18de11c8f767fdca2c7ebb0d4fa8bfe03c4f169cfea2aba2",
                "storage_address": "http://testserver/model/7b3183a99222df2b18de11c8f767fdca2c7ebb0d4fa8bfe03c4f169cfea2aba2/file/"
            },
            "permissions": {
                "process": {
                    "public": True,
                    "authorized_ids": []
                }
            },
            "rank": 0,
            "status": "done",
            "tag": ""
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "compute_plan_id": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintuple_key": "",
            "traintuple_type": ""
        },
        "non_certified_testtuples": None
    },
    {
        "traintuple": {
            "key": "5e18aef8-a674-8b22-0c82-532c39b29715",
            "algo": {
                "key": "ebbd8c65-dfe0-7d82-6d69-2f806deceffd",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_traintuple_execution_failure - Algo 0",
                "hash": "ebbd8c65dfe07d826d692f806deceffd296e715fa4db9e652304180dd7ee293d",
                "storage_address": "http://testserver/algo/ebbd8c65-dfe0-7d82-6d69-2f806deceffd/file/"
            },
            "creator": "MyOrg1MSP",
        "dataset": {
                "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e26-3959-8c42-bbf9-aba8d223c6a5",
                    "51d906cc-10b2-9eb8-1c93-5550b7508119",
                    "5702a4f5-61da-7827-35e2-e5d7b03605ee",
                    "8524b404-cc1b-2531-4fce-92b8c31da7b1"
                ],
                "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "compute_plan_id": "",
            "in_models": None,
            "log": "[00-01-0117-d64af6f]",
            "metadata": {},
            "out_model": None,
            "permissions": {
                "process": {
                    "public": True,
                    "authorized_ids": []
                }
            },
            "rank": 0,
            "status": "failed",
            "tag": ""
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "compute_plan_id": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintuple_key": "",
            "traintuple_type": ""
        },
        "non_certified_testtuples": None
    },
    {
        "composite_traintuple": {
            "key": "2978ca1f-7d55-20ef-42a8-2c86a2e24d5b",
            "algo": {
                "key": "09abcf99-a672-c0b9-5b3d-2431169e34ec",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuples_execution - Algo 0",
                "hash": "09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf",
                "storage_address": "http://testserver/composite_algo/09abcf99-a672-c0b9-5b3d-2431169e34ec/file/"
            },
            "creator": "MyOrg1MSP",
        "dataset": {
                "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e26-3959-8c42-bbf9-aba8d223c6a5",
                    "51d906cc-10b2-9eb8-1c93-5550b7508119",
                    "5702a4f5-61da-7827-35e2-e5d7b03605ee",
                    "8524b404-cc1b-2531-4fce-92b8c31da7b1"
                ],
                "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "compute_plan_id": "",
            "in_head_model": {
                "traintuple_key": "aa9be143-edc6-ef05-1ea2-55fd77bb54ba",
                "hash": "64c72dc39772e122ef552d10ff101ef6cee94935a84678a0125f7c3fd044dff8",
                "storage_address": ""
            },
            "in_trunk_model": {
                "traintuple_key": "aa9be143-edc6-ef05-1ea2-55fd77bb54ba",
                "hash": "00009a1256f8ce55ed907221000035daf1ac28111b5a3a03289da2f0601edf8f",
                "storage_address": "http://testserver/model/00009a1256f8ce55ed907221000035daf1ac28111b5a3a03289da2f0601edf8f/file/"
            },
            "log": "",
            "metadata": {},
            "out_head_model": {
                "out_model": {
                    "hash": "349b475ebd9458739af8685b8b75d7aeb1290209eabadad1b9b8afaa2b05c8d5"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "out_trunk_model": {
                "out_model": {
                    "key": "692e3f70-b9eb-fca3-c2e5-1e2a92c18092",
                    "hash": "692e3f70b9ebfca3c2e51e2a92c18092cc24dda547debefd6eb4bdd38ca6d803",
                    "storage_address": "http://testserver/model/692e3f70b9ebfca3c2e51e2a92c18092cc24dda547debefd6eb4bdd38ca6d803/file/"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": [
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
                "key": "09abcf99-a672-c0b9-5b3d-2431169e34ec",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuples_execution - Algo 0",
                "hash": "09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf",
                "storage_address": "http://testserver/composite_algo/09abcf99-a672-c0b9-5b3d-2431169e34ec/file/"
            },
            "certified": True,
            "compute_plan_id": "",
            "creator": "MyOrg1MSP",
        "dataset": {
                "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
                "worker": "MyOrg1MSP",
                "keys": [
                    "ffed4147-ffff-f2f1-8130-b7332c1460ec"
                ],
                "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "perf": 32
            },
            "key": "8cd0eb9a-e234-9fc3-3b36-ebb689963840",
            "log": "",
            "metadata": {},
            "objective": {
                "key": "48cc5ce4-d352-b859-e202-adb0d639ee09",
                "metrics": {
                    "hash": "0d64f855e07524da60203067713ab08fd6e479a02ebcb70364b2c6a2a29367e1",
                    "storage_address": "http://testserver/objective/48cc5ce4-d352-b859-e202-adb0d639ee09/metrics/"
                }
            },
            "rank": 0,
            "status": "done",
            "tag": "",
            "traintuple_key": "2978ca1f-7d55-20ef-42a8-2c86a2e24d5b",
            "traintuple_type": "composite_traintuple"
        },
        "non_certified_testtuples": None
    },
    {
        "composite_traintuple": {
            "key": "aa9be143-edc6-ef05-1ea2-55fd77bb54ba",
            "algo": {
                "key": "09abcf99-a672-c0b9-5b3d-2431169e34ec",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuples_execution - Algo 0",
                "hash": "09abcf99a672c0b95b3d2431169e34ec6bcc5154629db86c5d6aebb94377cbbf",
                "storage_address": "http://testserver/composite_algo/09abcf99-a672-c0b9-5b3d-2431169e34ec/file/"
            },
            "creator": "MyOrg1MSP",
        "dataset": {
                "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e26-3959-8c42-bbf9-aba8d223c6a5",
                    "51d906cc-10b2-9eb8-1c93-5550b7508119",
                    "5702a4f5-61da-7827-35e2-e5d7b03605ee",
                    "8524b404-cc1b-2531-4fce-92b8c31da7b1"
                ],
                "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "compute_plan_id": "",
            "in_head_model": None,
            "in_trunk_model": None,
            "log": "",
            "metadata": {},
            "out_head_model": {
                "out_model": {
                    "hash": "64c72dc39772e122ef552d10ff101ef6cee94935a84678a0125f7c3fd044dff8"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "out_trunk_model": {
                "out_model": {
                    "key": "00009a12-56f8-ce55-ed90-7221000035da",
                    "hash": "00009a1256f8ce55ed907221000035daf1ac28111b5a3a03289da2f0601edf8f",
                    "storage_address": "http://testserver/model/00009a1256f8ce55ed907221000035daf1ac28111b5a3a03289da2f0601edf8f/file/"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": [
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
            "compute_plan_id": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintuple_key": "",
            "traintuple_type": ""
        },
        "non_certified_testtuples": None
    },
    {
        "composite_traintuple": {
            "key": "2d3e98fb-eafe-bf19-95db-3ab205b9f803",
            "algo": {
                "key": "0fbb505a-32ae-8785-c08d-37fe7bf7476d",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_composite_traintuple_execution_failure - Algo 0",
                "hash": "0fbb505a32ae8785c08d37fe7bf7476d7365c3a0cef7c6e05c61c06db3267593",
                "storage_address": "http://testserver/composite_algo/0fbb505a-32ae-8785-c08d-37fe7bf7476d/file/"
            },
            "creator": "MyOrg1MSP",
        "dataset": {
                "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e26-3959-8c42-bbf9-aba8d223c6a5",
                    "51d906cc-10b2-9eb8-1c93-5550b7508119",
                    "5702a4f5-61da-7827-35e2-e5d7b03605ee",
                    "8524b404-cc1b-2531-4fce-92b8c31da7b1"
                ],
                "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "compute_plan_id": "",
            "in_head_model": None,
            "in_trunk_model": None,
            "log": "[00-01-0117-d390d32]",
            "metadata": {},
            "out_head_model": {
                "out_model": None,
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "out_trunk_model": {
                "out_model": None,
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": [
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
            "compute_plan_id": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintuple_key": "",
            "traintuple_type": ""
        },
        "non_certified_testtuples": None
    },
    {
        "composite_traintuple": {
            "key": "7dbd4b2a-c9e8-1b6d-edd7-75809e0903d8",
            "algo": {
                "key": "5a9fc103-2bd9-7c9e-baaf-eaf7d2e5d81f",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple_execution_failure - Algo 0",
                "hash": "5a9fc1032bd97c9ebaafeaf7d2e5d81f375f1ff8e13ad3000e43f135eb47810c",
                "storage_address": "http://testserver/composite_algo/5a9fc103-2bd9-7c9e-baaf-eaf7d2e5d81f/file/"
            },
            "creator": "MyOrg1MSP",
        "dataset": {
                "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e26-3959-8c42-bbf9-aba8d223c6a5"
                ],
                "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "compute_plan_id": "",
            "in_head_model": None,
            "in_trunk_model": None,
            "log": "",
            "metadata": {},
            "out_head_model": {
                "out_model": {
                    "hash": "8b87222907027a470d6d99409b0de9a9ced07142d026ab875d6ddfdecf9db96d"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "out_trunk_model": {
                "out_model": {
                    "key": "fcfcaa4f-3be7-3940-006f-c54566b2946f",
                    "hash": "fcfcaa4f3be73940006fc54566b2946fabd5ee677496a5dd43e4b8c0c3c3d54d",
                    "storage_address": "http://testserver/model/fcfcaa4f3be73940006fc54566b2946fabd5ee677496a5dd43e4b8c0c3c3d54d/file/"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": [
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
            "compute_plan_id": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintuple_key": "",
            "traintuple_type": ""
        },
        "non_certified_testtuples": None
    },
    {
        "composite_traintuple": {
            "key": "df3e1942-6496-a5b8-a79d-8f1b96e52de9",
            "algo": {
                "key": "5a9fc103-2bd9-7c9e-baaf-eaf7d2e5d81f",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple_execution_failure - Algo 0",
                "hash": "5a9fc1032bd97c9ebaafeaf7d2e5d81f375f1ff8e13ad3000e43f135eb47810c",
                "storage_address": "http://testserver/composite_algo/5a9fc103-2bd9-7c9e-baaf-eaf7d2e5d81f/file/"
            },
            "creator": "MyOrg1MSP",
        "dataset": {
                "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
                "worker": "MyOrg1MSP",
                "keys": [
                    "51d906cc-10b2-9eb8-1c93-5550b7508119"
                ],
                "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "compute_plan_id": "",
            "in_head_model": None,
            "in_trunk_model": None,
            "log": "",
            "metadata": {},
            "out_head_model": {
                "out_model": {
                    "hash": "bffb89749a253de1d451a836748dc813035dbcacb01fb85911b97c577c10ea6d"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "out_trunk_model": {
                "out_model": {
                    "key": "682d31d9-e956-54ed-0aaf-81184136d87c",
                    "hash": "682d31d9e95654ed0aaf81184136d87c7ff2a0046c3d24181508f112d58b330d",
                    "storage_address": "http://testserver/model/682d31d9e95654ed0aaf81184136d87c7ff2a0046c3d24181508f112d58b330d/file/"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": [
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
            "compute_plan_id": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintuple_key": "",
            "traintuple_type": ""
        },
        "non_certified_testtuples": None
    },
    {
        "composite_traintuple": {
            "key": "3197bd6c-56bc-4708-9864-c76b47b6115e",
            "algo": {
                "key": "fe2eba45-66fa-c967-ef84-7cbb3a8eba75",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
                "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
                "storage_address": "http://testserver/composite_algo/fe2eba45-66fa-c967-ef84-7cbb3a8eba75/file/"
            },
            "creator": "MyOrg1MSP",
        "dataset": {
                "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
                "worker": "MyOrg1MSP",
                "keys": [
                    "265f1e26-3959-8c42-bbf9-aba8d223c6a5"
                ],
                "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "compute_plan_id": "",
            "in_head_model": None,
            "in_trunk_model": None,
            "log": "",
            "metadata": {},
            "out_head_model": {
                "out_model": {
                    "hash": "7d7ed2eac5e822ea90058387dd35d1270639ecc4982a6d72b619b8659813163a"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "out_trunk_model": {
                "out_model": {
                    "key": "b312a262-592a-a7ed-56a0-7d0eb02bec05",
                    "hash": "b312a262592aa7ed56a07d0eb02bec0548745eb7316d4ea86b3719b2497d8cb2",
                    "storage_address": "http://testserver/model/b312a262592aa7ed56a07d0eb02bec0548745eb7316d4ea86b3719b2497d8cb2/file/"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": [
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
            "compute_plan_id": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintuple_key": "",
            "traintuple_type": ""
        },
        "non_certified_testtuples": None
    },
    {
        "composite_traintuple": {
            "key": "3be92d96-d1ab-dabf-be6a-4ff612d70f7f",
            "algo": {
                "key": "fe2eba45-66fa-c967-ef84-7cbb3a8eba75",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
                "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
                "storage_address": "http://testserver/composite_algo/fe2eba45-66fa-c967-ef84-7cbb3a8eba75/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg2MSP",
                "keys": [
                    "70474091-7e35-b366-48b8-0d9826e1f24d"
                ],
                "opener_hash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
                "metadata": {}
            },
            "compute_plan_id": "",
            "in_head_model": {
                "traintuple_key": "e7b96818-eadc-dce6-940c-16b388bbd264",
                "hash": "3af8f86ed9fe07237497e52d1ced195d7e4752f7d130327929f96ea688d60a41",
                "storage_address": ""
            },
            "in_trunk_model": {
                "traintuple_key": "9cb5582f-c3e8-22b9-ddab-bf7479097df0",
                "hash": "4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688",
                "storage_address": "http://testserver/model/4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688/file/"
            },
            "log": "",
            "metadata": {},
            "out_head_model": {
                "out_model": {
                    "hash": "8b6a7f3b7feef0a2c157bf2acfd2596fd7815a0a69b0a41b7451bab47d022eaa"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": [
                            "MyOrg2MSP"
                        ]
                    }
                }
            },
            "out_trunk_model": {
                "out_model": {
                    "key": "66392ca3-e6a5-935f-b8e2-2a5ee5b8af31",
                    "hash": "66392ca3e6a5935fb8e22a5ee5b8af31dbec5655ff087b98f071abf7e4f3ce74",
                    "storage_address": "http://backend-org-2-substra-backend-server.org-2:8000/model/66392ca3e6a5935fb8e22a5ee5b8af31dbec5655ff087b98f071abf7e4f3ce74/file/"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": [
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
                "key": "fe2eba45-66fa-c967-ef84-7cbb3a8eba75",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
                "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
                "storage_address": "http://testserver/composite_algo/fe2eba45-66fa-c967-ef84-7cbb3a8eba75/file/"
            },
            "certified": True,
            "compute_plan_id": "",
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg2MSP",
                "keys": [
                    "edaa4ccd-fc9b-cadd-a859-498fbb550a6e"
                ],
                "opener_hash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
                "perf": 32
            },
            "key": "87e83565-0d84-ca0c-f26a-c332bad4f4d7",
            "log": "",
            "metadata": {},
            "objective": {
                "key": "b61067ad-c59f-b1aa-be21-eab767d986cc",
                "metrics": {
                    "hash": "1a61bea02e3e75f8197d682cbaa6110c9709fbfbd4f16964acc390c70e7a22fe",
                    "storage_address": "http://backend-org-2-substra-backend-server.org-2:8000/objective/b61067ad-c59f-b1aa-be21-eab767d986cc/metrics/"
                }
            },
            "rank": 0,
            "status": "done",
            "tag": "",
            "traintuple_key": "3be92d96-d1ab-dabf-be6a-4ff612d70f7f",
            "traintuple_type": "composite_traintuple"
        },
        "non_certified_testtuples": None
    },
    {
        "composite_traintuple": {
            "key": "5adbd24e-a21c-b23b-1ffc-65151038a62c",
            "algo": {
                "key": "fe2eba45-66fa-c967-ef84-7cbb3a8eba75",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
                "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
                "storage_address": "http://testserver/composite_algo/fe2eba45-66fa-c967-ef84-7cbb3a8eba75/file/"
            },
            "creator": "MyOrg1MSP",
        "dataset": {
                "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
                "worker": "MyOrg1MSP",
                "keys": [
                    "51d906cc-10b2-9eb8-1c93-5550b7508119"
                ],
                "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "metadata": {}
            },
            "compute_plan_id": "",
            "in_head_model": {
                "traintuple_key": "3197bd6c-56bc-4708-9864-c76b47b6115e",
                "hash": "7d7ed2eac5e822ea90058387dd35d1270639ecc4982a6d72b619b8659813163a",
                "storage_address": ""
            },
            "in_trunk_model": {
                "traintuple_key": "9cb5582f-c3e8-22b9-ddab-bf7479097df0",
                "hash": "4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688",
                "storage_address": "http://testserver/model/4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688/file/"
            },
            "log": "",
            "metadata": {},
            "out_head_model": {
                "out_model": {
                    "hash": "28a705e08e765569bd89262f821e1c7285e43fa1e82df2f833464b8ff890c7bd"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": [
                            "MyOrg1MSP"
                        ]
                    }
                }
            },
            "out_trunk_model": {
                "out_model": {
                    "key": "14b7e325-4896-db4f-43c5-82695c39d096",
                    "hash": "14b7e3254896db4f43c582695c39d096f33e1390e3ecaa8b0e6e7619bf827044",
                    "storage_address": "http://testserver/model/14b7e3254896db4f43c582695c39d096f33e1390e3ecaa8b0e6e7619bf827044/file/"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": [
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
                "key": "fe2eba45-66fa-c967-ef84-7cbb3a8eba75",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
                "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
                "storage_address": "http://testserver/composite_algo/fe2eba45-66fa-c967-ef84-7cbb3a8eba75/file/"
            },
            "certified": True,
            "compute_plan_id": "",
            "creator": "MyOrg1MSP",
        "dataset": {
                "key": "e25a6ac0-b496-6c72-a339-45bdeb1f9f6f",
                "worker": "MyOrg1MSP",
                "keys": [
                    "ffed4147-ffff-f2f1-8130-b7332c1460ec"
                ],
                "opener_hash": "e25a6ac0b4966c72a33945bdeb1f9f6f870df595ebf9273fe61c7e5c2bc77204",
                "perf": 32
            },
            "key": "6075c796-cc47-0f1e-1de7-b98d8a4d28b1",
            "log": "",
            "metadata": {},
            "objective": {
                "key": "48cc5ce4-d352-b859-e202-adb0d639ee09",
                "metrics": {
                    "hash": "0d64f855e07524da60203067713ab08fd6e479a02ebcb70364b2c6a2a29367e1",
                    "storage_address": "http://testserver/objective/48cc5ce4-d352-b859-e202-adb0d639ee09/metrics/"
                }
            },
            "rank": 0,
            "status": "done",
            "tag": "",
            "traintuple_key": "5adbd24e-a21c-b23b-1ffc-65151038a62c",
            "traintuple_type": "composite_traintuple"
        },
        "non_certified_testtuples": None
    },
    {
        "composite_traintuple": {
            "key": "e7b96818-eadc-dce6-940c-16b388bbd264",
            "algo": {
                "key": "fe2eba45-66fa-c967-ef84-7cbb3a8eba75",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 0",
                "hash": "fe2eba4566fac967ef847cbb3a8eba75fa7c03291e4db621bf3bc27b54b7ed87",
                "storage_address": "http://testserver/composite_algo/fe2eba45-66fa-c967-ef84-7cbb3a8eba75/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg2MSP",
                "keys": [
                    "26e52856-b272-61fc-12e9-615d5914027d"
                ],
                "opener_hash": "aa572a964b024435d48a73aacb86e3d195614a4f335e739116bad2c427a1fb02",
                "metadata": {}
            },
            "compute_plan_id": "",
            "in_head_model": None,
            "in_trunk_model": None,
            "log": "",
            "metadata": {},
            "out_head_model": {
                "out_model": {
                    "hash": "3af8f86ed9fe07237497e52d1ced195d7e4752f7d130327929f96ea688d60a41"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": [
                            "MyOrg2MSP"
                        ]
                    }
                }
            },
            "out_trunk_model": {
                "out_model": {
                    "key": "cd8a895a-9b60-4ccb-b2e2-bf9f081d0560",
                    "hash": "cd8a895a9b604ccbb2e2bf9f081d0560bfd86f4a98beabd833d4c7c36f35cd9d",
                    "storage_address": "http://backend-org-2-substra-backend-server.org-2:8000/model/cd8a895a9b604ccbb2e2bf9f081d0560bfd86f4a98beabd833d4c7c36f35cd9d/file/"
                },
                "permissions": {
                    "process": {
                        "public": False,
                        "authorized_ids": [
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
            "compute_plan_id": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintuple_key": "",
            "traintuple_type": ""
        },
        "non_certified_testtuples": None
    },
    {
        "aggregatetuple": {
            "key": "9936e27a-5738-298e-39e4-308c0d4d612a",
            "algo": {
                "key": "16acae7a-5d70-2a97-c4cc-e626bbe5c44d",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple_execution_failure - Algo 1",
                "hash": "16acae7a5d702a97c4cce626bbe5c44d367d73617ee42e81660bce7494379986",
                "storage_address": "http://testserver/aggregate_algo/16acae7a-5d70-2a97-c4cc-e626bbe5c44d/file/"
            },
            "creator": "MyOrg1MSP",
            "compute_plan_id": "",
            "log": "[00-01-0117-a45d457]",
            "metadata": {},
            "in_models": [
                {
                    "traintuple_key": "7dbd4b2a-c9e8-1b6d-edd7-75809e0903d8",
                    "hash": "fcfcaa4f3be73940006fc54566b2946fabd5ee677496a5dd43e4b8c0c3c3d54d",
                    "storage_address": "http://testserver/model/fcfcaa4f3be73940006fc54566b2946fabd5ee677496a5dd43e4b8c0c3c3d54d/file/"
                },
                {
                    "traintuple_key": "df3e1942-6496-a5b8-a79d-8f1b96e52de9",
                    "hash": "682d31d9e95654ed0aaf81184136d87c7ff2a0046c3d24181508f112d58b330d",
                    "storage_address": "http://testserver/model/682d31d9e95654ed0aaf81184136d87c7ff2a0046c3d24181508f112d58b330d/file/"
                }
            ],
            "out_model": None,
            "rank": 0,
            "status": "failed",
            "tag": "",
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
                        "MyOrg1MSP"
                    ]
                }
            },
            "worker": "MyOrg1MSP"
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "compute_plan_id": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintuple_key": "",
            "traintuple_type": ""
        },
        "non_certified_testtuples": None
    },
    {
        "aggregatetuple": {
            "key": "0c6d7947-0e53-6e73-9062-3b37622228b5",
            "algo": {
                "key": "25081cda-2aab-5915-fe1d-732c6483e24e",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregatetuple - Algo 1",
                "hash": "25081cda2aab5915fe1d732c6483e24ef8fb2484a6e856c8ed912b36577d3d9a",
                "storage_address": "http://testserver/aggregate_algo/25081cda-2aab-5915-fe1d-732c6483e24e/file/"
            },
            "creator": "MyOrg1MSP",
            "compute_plan_id": "",
            "log": "",
            "metadata": {},
            "in_models": [
                {
                    "traintuple_key": "3169bb17-2502-f675-56a6-f12b856a5d65",
                    "hash": "940262c35a6b33c2b7c8811fa785899b00e287ffa05e3cb5a23c857e9c89c760",
                    "storage_address": "http://testserver/model/940262c35a6b33c2b7c8811fa785899b00e287ffa05e3cb5a23c857e9c89c760/file/"
                },
                {
                    "traintuple_key": "ea7180cc-c125-dcce-ff10-400fd2943f1e",
                    "hash": "02ccc4eeb426f7bbfe746a06a4c63a2023a8f2ea2c72f92242cc5f7f1164383c",
                    "storage_address": "http://testserver/model/02ccc4eeb426f7bbfe746a06a4c63a2023a8f2ea2c72f92242cc5f7f1164383c/file/"
                },
                {
                    "traintuple_key": "a9c586b7-2c9c-1141-2b0c-9f81d599651a",
                    "hash": "f33d3c7a21e97f5f0edd636f3b313c6a7757cc458614e49da74d58af7fc0c4c2",
                    "storage_address": "http://testserver/model/f33d3c7a21e97f5f0edd636f3b313c6a7757cc458614e49da74d58af7fc0c4c2/file/"
                }
            ],
            "out_model": {
                "key": "bd2e6a51-0edc-1197-4e3d-8b5459f0d4bd",
                "hash": "bd2e6a510edc11974e3d8b5459f0d4bd9b3169afe1fa47643147351f51fb18ac",
                "storage_address": "http://testserver/model/bd2e6a510edc11974e3d8b5459f0d4bd9b3169afe1fa47643147351f51fb18ac/file/"
            },
            "rank": 0,
            "status": "done",
            "tag": "",
            "permissions": {
                "process": {
                    "public": True,
                    "authorized_ids": []
                }
            },
            "worker": "MyOrg1MSP"
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "compute_plan_id": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintuple_key": "",
            "traintuple_type": ""
        },
        "non_certified_testtuples": None
    },
    {
        "aggregatetuple": {
            "key": "9cb5582f-c3e8-22b9-ddab-bf7479097df0",
            "algo": {
                "key": "57648509-5a2f-9bc7-8ed6-238b847c9c67",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 1",
                "hash": "576485095a2f9bc78ed6238b847c9c679fb755b822c0cc6e08e60ea227ec0648",
                "storage_address": "http://testserver/aggregate_algo/57648509-5a2f-9bc7-8ed6-238b847c9c67/file/"
            },
            "creator": "MyOrg1MSP",
            "compute_plan_id": "",
            "log": "",
            "metadata": {},
            "in_models": [
                {
                    "traintuple_key": "3197bd6c-56bc-4708-9864-c76b47b6115e",
                    "hash": "b312a262592aa7ed56a07d0eb02bec0548745eb7316d4ea86b3719b2497d8cb2",
                    "storage_address": "http://testserver/model/b312a262592aa7ed56a07d0eb02bec0548745eb7316d4ea86b3719b2497d8cb2/file/"
                },
                {
                    "traintuple_key": "e7b96818-eadc-dce6-940c-16b388bbd264",
                    "hash": "cd8a895a9b604ccbb2e2bf9f081d0560bfd86f4a98beabd833d4c7c36f35cd9d",
                    "storage_address": "http://backend-org-2-substra-backend-server.org-2:8000/model/cd8a895a9b604ccbb2e2bf9f081d0560bfd86f4a98beabd833d4c7c36f35cd9d/file/"
                }
            ],
            "out_model": {
                "key": "4e9f3d4b-8575-c5cd-a471-88043bd8e0f4",
                "hash": "4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688",
                "storage_address": "http://testserver/model/4e9f3d4b8575c5cda47188043bd8e0f43fef42e2cf92f2476ac78bda096f2688/file/"
            },
            "rank": 0,
            "status": "done",
            "tag": "",
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
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
            "compute_plan_id": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintuple_key": "",
            "traintuple_type": ""
        },
        "non_certified_testtuples": None
    },
    {
        "aggregatetuple": {
            "key": "d57e8f35-97a9-c065-d02c-65c5a6def14b",
            "algo": {
                "key": "57648509-5a2f-9bc7-8ed6-238b847c9c67",
                "name": "9224cad96c964b7b8ed2f7eb5872c27a_test_aggregate_composite_traintuples - Algo 1",
                "hash": "576485095a2f9bc78ed6238b847c9c679fb755b822c0cc6e08e60ea227ec0648",
                "storage_address": "http://testserver/aggregate_algo/57648509-5a2f-9bc7-8ed6-238b847c9c67/file/"
            },
            "creator": "MyOrg1MSP",
            "compute_plan_id": "",
            "log": "",
            "metadata": {},
            "in_models": [
                {
                    "traintuple_key": "5adbd24e-a21c-b23b-1ffc-65151038a62c",
                    "hash": "14b7e3254896db4f43c582695c39d096f33e1390e3ecaa8b0e6e7619bf827044",
                    "storage_address": "http://testserver/model/14b7e3254896db4f43c582695c39d096f33e1390e3ecaa8b0e6e7619bf827044/file/"
                },
                {
                    "traintuple_key": "3be92d96-d1ab-dabf-be6a-4ff612d70f7f",
                    "hash": "66392ca3e6a5935fb8e22a5ee5b8af31dbec5655ff087b98f071abf7e4f3ce74",
                    "storage_address": "http://backend-org-2-substra-backend-server.org-2:8000/model/66392ca3e6a5935fb8e22a5ee5b8af31dbec5655ff087b98f071abf7e4f3ce74/file/"
                }
            ],
            "out_model": {
                "key": "d62bd637-d422-3726-e96c-46337539da3b",
                "hash": "d62bd637d4223726e96c46337539da3bbd94dc3a3b4f233f1c7152dd3b02364d",
                "storage_address": "http://testserver/model/d62bd637d4223726e96c46337539da3bbd94dc3a3b4f233f1c7152dd3b02364d/file/"
            },
            "rank": 0,
            "status": "done",
            "tag": "",
            "permissions": {
                "process": {
                    "public": False,
                    "authorized_ids": [
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
            "compute_plan_id": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "metadata": None,
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintuple_key": "",
            "traintuple_type": ""
        },
        "non_certified_testtuples": None
    }
]

