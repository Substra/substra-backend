objective = [
    {
        "key": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
        "name": "Skin Lesion Classification Objective",
        "description": {
            "hash": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
            "storageAddress": "http://testserver/objective/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/description/"
        },
        "metrics": {
            "name": "macro-average recall",
            "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
            "storageAddress": "http://testserver/objective/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/metrics/"
        },
        "owner": "3ab9763cc352dca85802c4e7579d50512283719e375ef4e256a73c5139f792ff",
        "testData": {
            "dataManagerKey": "9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528",
            "dataKeys": [
                "e11aeec290749e4c50c91305e10463eced8dbf3808971ec0c6ea0e36cb7ab3e1",
                "4b5152871b181d10ee774c10458c064c70710f4ba35938f10c0b7aa51f7dc010"
            ],
        },
        "permissions": "all"
    }
]

datamanager = [
    {
        "objectiveKey": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
        "description": {
            "hash": "7a90514f88c70002608a9868681dd1589ea598e78d00a8cd7783c3ea0f9ceb09",
            "storageAddress": "http://testserver/data_manager/59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd/description/"
        },
        "key": "59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd",
        "name": "ISIC 2018",
        "opener": {
            "hash": "59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd",
            "storageAddress": "http://testserver/data_manager/59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd/opener/"
        },
        "owner": "3ab9763cc352dca85802c4e7579d50512283719e375ef4e256a73c5139f792ff",
        "permissions": "all",
        "type": "Images"
    },
    {
        "objectiveKey": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
        "description": {
            "hash": "258bef187a166b3fef5cb86e68c8f7e154c283a148cd5bc344fec7e698821ad3",
            "storageAddress": "http://testserver/data_manager/9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528/description/"
        },
        "key": "9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528",
        "name": "Simplified ISIC 2018",
        "opener": {
            "hash": "9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528",
            "storageAddress": "http://testserver/data_manager/9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528/opener/"
        },
        "owner": "3ab9763cc352dca85802c4e7579d50512283719e375ef4e256a73c5139f792ff",
        "permissions": "all",
        "type": "Images"
    }
]

algo = [
    {
        "key": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f",
        "name": "Neural Network",
        "content": {
            "hash": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f",
            "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/file/"
        },
        "description": {
            "hash": "b9463411a01ea00869bdffce6e59a5c100a4e635c0a9386266cad3c77eb28e9e",
            "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/description/"
        },
        "owner": "3ab9763cc352dca85802c4e7579d50512283719e375ef4e256a73c5139f792ff",
        "objectiveKey": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
        "permissions": "all"
    },
    {
        "key": "da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b",
        "name": "Logistic regression",
        "content": {
            "hash": "da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b",
            "storageAddress": "http://testserver/algo/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/file/"
        },
        "description": {
            "hash": "124a0425b746d7072282d167b53cb6aab3a31bf1946dae89135c15b0126ebec3",
            "storageAddress": "http://testserver/algo/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/description/"
        },
        "owner": "3ab9763cc352dca85802c4e7579d50512283719e375ef4e256a73c5139f792ff",
        "objectiveKey": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
        "permissions": "all"
    },
    {
        "key": "f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284",
        "name": "Random Forest",
        "content": {
            "hash": "f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284",
            "storageAddress": "http://testserver/algo/f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284/file/"
        },
        "description": {
            "hash": "4acea40c4b51996c88ef279c5c9aa41ab77b97d38c5ca167e978a98b2e402675",
            "storageAddress": "http://testserver/algo/f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284/description/"
        },
        "owner": "3ab9763cc352dca85802c4e7579d50512283719e375ef4e256a73c5139f792ff",
        "objectiveKey": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
        "permissions": "all"
    }
]

traintuple = [
    {
        "algo": {
            "hash": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f",
            "name": "Neural Network",
            "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/file/"
        },
        "objective": {
            "hash": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
            "metrics": {
                "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
                "storageAddress": "http://testserver/objective/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/metrics/"
            }
        },
        "creator": "3ab9763cc352dca85802c4e7579d50512283719e375ef4e256a73c5139f792ff",
        "data": {
            "keys": [
                "62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a",
                "42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9"
            ],
            "openerHash": "59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd",
            "perf": 0,
            "worker": "3ab9763cc352dca85802c4e7579d50512283719e375ef4e256a73c5139f792ff"
        },
        "fltask": "",
        "inModels": None,
        "key": "65653083beb385b6626ef2ad2c9b898601c6b0d3e764b49b87a9203bdd5019a8",
        "log": "[00-01-0032-aad2202]",
        "outModel": None,
        "permissions": "all",
        "rank": 0,
        "status": "failed"
    },
    {
        "algo": {
            "hash": "da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b",
            "name": "Logistic regression",
            "storageAddress": "http://testserver/algo/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/file/"
        },
        "objective": {
            "hash": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
            "metrics": {
                "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
                "storageAddress": "http://testserver/objective/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/metrics/"
            }
        },
        "creator": "3ab9763cc352dca85802c4e7579d50512283719e375ef4e256a73c5139f792ff",
        "data": {
            "keys": [
                "62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a",
                "42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9"
            ],
            "openerHash": "59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd",
            "perf": 1,
            "worker": "3ab9763cc352dca85802c4e7579d50512283719e375ef4e256a73c5139f792ff"
        },
        "fltask": "",
        "inModels": None,
        "key": "5a4bb9c415b6e927803027acd50680d585b349a12e22314d2869f23128cf1cdb",
        "log": "Train - CPU:75.57 % - Mem:0.11 GB - GPU:0.00 % - GPU Mem:0.00 GB; ",
        "outModel": {
            "hash": "f40783150d90812e6f2c07f0feea0b7d6eb8673635aa96fa20a775c324d21446",
            "storageAddress": "http://testserver/model/f40783150d90812e6f2c07f0feea0b7d6eb8673635aa96fa20a775c324d21446/file/"
        },
        "permissions": "all",
        "rank": 0,
        "status": "done"
    },
    {
        "algo": {
            "hash": "f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284",
            "name": "Random Forest",
            "storageAddress": "http://testserver/algo/f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284/file/"
        },
        "objective": {
            "hash": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
            "metrics": {
                "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
                "storageAddress": "http://testserver/objective/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/metrics/"
            }
        },
        "creator": "3ab9763cc352dca85802c4e7579d50512283719e375ef4e256a73c5139f792ff",
        "data": {
            "keys": [
                "62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a",
                "42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9"
            ],
            "openerHash": "59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd",
            "perf": 0,
            "worker": "3ab9763cc352dca85802c4e7579d50512283719e375ef4e256a73c5139f792ff"
        },
        "fltask": "",
        "inModels": None,
        "key": "da1e515587e030449c1ab2042441d88e606fc5f54df9b69ad4215ae8d12b4cea",
        "log": "[00-01-0032-db9e321]",
        "outModel": None,
        "permissions": "all",
        "rank": 0,
        "status": "failed"
    }
]

testtuple = [
    {
        "objective": {
            "hash": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
            "metrics": {
                "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
                "storageAddress": "http://testserver/objective/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/metrics/"
            }
        },
        "algo": {
            "name": "Logistic regression",
            "hash": "da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b",
            "storageAddress": "http://testserver/algo/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/file/"
        },
        "model": {
            "traintupleKey": "5a4bb9c415b6e927803027acd50680d585b349a12e22314d2869f23128cf1cdb",
            "hash": "f40783150d90812e6f2c07f0feea0b7d6eb8673635aa96fa20a775c324d21446",
            "storageAddress": "http://testserver/model/f40783150d90812e6f2c07f0feea0b7d6eb8673635aa96fa20a775c324d21446/file/"
        },
        "data": {
            "worker": "3ab9763cc352dca85802c4e7579d50512283719e375ef4e256a73c5139f792ff",
            "keys": [
                "4b5152871b181d10ee774c10458c064c70710f4ba35938f10c0b7aa51f7dc010",
                "e11aeec290749e4c50c91305e10463eced8dbf3808971ec0c6ea0e36cb7ab3e1"
            ],
            "openerHash": "9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528",
            "perf": 1
        },
        "certified": True,
        "status": "done",
        "log": "Test - CPU:0.00 % - Mem:0.00 GB - GPU:0.00 % - GPU Mem:0.00 GB; ",
        "permissions": "all",
        "creator": "3ab9763cc352dca85802c4e7579d50512283719e375ef4e256a73c5139f792ff"
    }
]

model = [
    {
        "testtuple": {
            "algo": {
                "hash": "da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b",
                "name": "Logistic regression",
                "storageAddress": "http://testserver/algo/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/file/"
            },
            "certified": True,
            "objective": {
                "hash": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
                "metrics": {
                    "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
                    "storageAddress": "http://testserver/objective/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/metrics/"
                }
            },
            "creator": "3ab9763cc352dca85802c4e7579d50512283719e375ef4e256a73c5139f792ff",
            "data": {
                "keys": [
                    "4b5152871b181d10ee774c10458c064c70710f4ba35938f10c0b7aa51f7dc010",
                    "e11aeec290749e4c50c91305e10463eced8dbf3808971ec0c6ea0e36cb7ab3e1"
                ],
                "openerHash": "9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528",
                "perf": 1,
                "worker": "3ab9763cc352dca85802c4e7579d50512283719e375ef4e256a73c5139f792ff"
            },
            "key": "d39993174379a92c94d5be9827b7e7b44c0f387964018ce88b0e066400797a41",
            "log": "Test - CPU:0.00 % - Mem:0.00 GB - GPU:0.00 % - GPU Mem:0.00 GB; ",
            "model": {
                "hash": "f40783150d90812e6f2c07f0feea0b7d6eb8673635aa96fa20a775c324d21446",
                "storageAddress": "http://testserver/model/f40783150d90812e6f2c07f0feea0b7d6eb8673635aa96fa20a775c324d21446/file/",
                "traintupleKey": "5a4bb9c415b6e927803027acd50680d585b349a12e22314d2869f23128cf1cdb"
            },
            "permissions": "all",
            "status": "done"
        },
        "traintuple": {
            "algo": {
                "hash": "da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b",
                "name": "Logistic regression",
                "storageAddress": "http://testserver/algo/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/file/"
            },
            "objective": {
                "hash": "d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f",
                "metrics": {
                    "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
                    "storageAddress": "http://testserver/objective/d5002e1cd50bd5de5341df8a7b7d11b6437154b3b08f531c9b8f93889855c66f/metrics/"
                }
            },
            "creator": "3ab9763cc352dca85802c4e7579d50512283719e375ef4e256a73c5139f792ff",
            "data": {
                "keys": [
                    "62fb3263208d62c7235a046ee1d80e25512fe782254b730a9e566276b8c0ef3a",
                    "42303efa663015e729159833a12ffb510ff92a6e386b8152f90f6fb14ddc94c9"
                ],
                "openerHash": "59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd",
                "perf": 1,
                "worker": "3ab9763cc352dca85802c4e7579d50512283719e375ef4e256a73c5139f792ff"
            },
            "fltask": "",
            "inModels": None,
            "key": "5a4bb9c415b6e927803027acd50680d585b349a12e22314d2869f23128cf1cdb",
            "log": "Train - CPU:75.57 % - Mem:0.11 GB - GPU:0.00 % - GPU Mem:0.00 GB; ",
            "outModel": {
                "hash": "f40783150d90812e6f2c07f0feea0b7d6eb8673635aa96fa20a775c324d21446",
                "storageAddress": "http://testserver/model/f40783150d90812e6f2c07f0feea0b7d6eb8673635aa96fa20a775c324d21446/file/"
            },
            "permissions": "all",
            "rank": 0,
            "status": "done"
        }
    }
]

