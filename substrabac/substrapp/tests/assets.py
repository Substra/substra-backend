objective = [
    {
        "key": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
        "name": "Skin Lesion Classification Objective",
        "description": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/description/"
        },
        "metrics": {
            "name": "macro-average recall",
            "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
            "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
        },
        "owner": "703433008d3f62dab5ffaccb3c53d723660f5f6cdac3c5dfd26ac88312b5a94e",
        "testDataset": {
            "dataManagerKey": "9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528",
            "dataSampleKeys": [
                "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf",
                "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a"
            ]
        },
        "permissions": "all"
    }
]

datamanager = [
    {
        "objectiveKey": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
        "description": {
            "hash": "15863c2af1fcfee9ca6f61f04be8a0eaaf6a45e4d50c421788d450d198e580f1",
            "storageAddress": "http://testserver/data_manager/59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd/description/"
        },
        "key": "59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd",
        "name": "ISIC 2018",
        "opener": {
            "hash": "59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd",
            "storageAddress": "http://testserver/data_manager/59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd/opener/"
        },
        "owner": "703433008d3f62dab5ffaccb3c53d723660f5f6cdac3c5dfd26ac88312b5a94e",
        "permissions": "all",
        "type": "Images"
    },
    {
        "objectiveKey": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
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
        "owner": "703433008d3f62dab5ffaccb3c53d723660f5f6cdac3c5dfd26ac88312b5a94e",
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
        "owner": "703433008d3f62dab5ffaccb3c53d723660f5f6cdac3c5dfd26ac88312b5a94e",
        "objectiveKey": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
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
        "owner": "703433008d3f62dab5ffaccb3c53d723660f5f6cdac3c5dfd26ac88312b5a94e",
        "objectiveKey": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
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
        "owner": "703433008d3f62dab5ffaccb3c53d723660f5f6cdac3c5dfd26ac88312b5a94e",
        "objectiveKey": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
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
        "creator": "703433008d3f62dab5ffaccb3c53d723660f5f6cdac3c5dfd26ac88312b5a94e",
        "dataset": {
            "keys": [
                "bcdda7da240f1de016e5c185d63027ff6536c233f7ed96d086766e99027d4e24",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd",
            "perf": 0,
            "worker": "703433008d3f62dab5ffaccb3c53d723660f5f6cdac3c5dfd26ac88312b5a94e"
        },
        "fltask": "",
        "inModels": None,
        "key": "dfa89a184b6ba5c50daa5a7176818fe1b1c5c3b781b30b99e4d79eef036006f2",
        "log": "[00-01-0032-456da5d]",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
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
        "creator": "703433008d3f62dab5ffaccb3c53d723660f5f6cdac3c5dfd26ac88312b5a94e",
        "dataset": {
            "keys": [
                "bcdda7da240f1de016e5c185d63027ff6536c233f7ed96d086766e99027d4e24",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd",
            "perf": 1,
            "worker": "703433008d3f62dab5ffaccb3c53d723660f5f6cdac3c5dfd26ac88312b5a94e"
        },
        "fltask": "",
        "inModels": None,
        "key": "66caabaf37455cc7af8e89cac37eb0ebfdf73ac7fe4765c644ea6340c2589c0a",
        "log": "Train - CPU:78.04 % - Mem:0.11 GB - GPU:0.00 % - GPU Mem:0.00 GB; ",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outModel": {
            "hash": "2bd56e309a7e899027a1e8b3990fd7a69986291043079d836bc2f8bcdb9ec8de",
            "storageAddress": "http://testserver/model/2bd56e309a7e899027a1e8b3990fd7a69986291043079d836bc2f8bcdb9ec8de/file/"
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
        "creator": "703433008d3f62dab5ffaccb3c53d723660f5f6cdac3c5dfd26ac88312b5a94e",
        "dataset": {
            "keys": [
                "bcdda7da240f1de016e5c185d63027ff6536c233f7ed96d086766e99027d4e24",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd",
            "perf": 0,
            "worker": "703433008d3f62dab5ffaccb3c53d723660f5f6cdac3c5dfd26ac88312b5a94e"
        },
        "fltask": "",
        "inModels": None,
        "key": "7f4bea1afafefda207daf7c24034aab4f1db0df0575ba6b303d3d7a6df1794e7",
        "log": "[00-01-0032-ea27bd6]",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outModel": None,
        "permissions": "all",
        "rank": 0,
        "status": "failed"
    }
]

testtuple = [
    {
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "algo": {
            "name": "Logistic regression",
            "hash": "da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b",
            "storageAddress": "http://testserver/algo/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/file/"
        },
        "model": {
            "traintupleKey": "66caabaf37455cc7af8e89cac37eb0ebfdf73ac7fe4765c644ea6340c2589c0a",
            "hash": "2bd56e309a7e899027a1e8b3990fd7a69986291043079d836bc2f8bcdb9ec8de",
            "storageAddress": "http://testserver/model/2bd56e309a7e899027a1e8b3990fd7a69986291043079d836bc2f8bcdb9ec8de/file/"
        },
        "dataset": {
            "worker": "703433008d3f62dab5ffaccb3c53d723660f5f6cdac3c5dfd26ac88312b5a94e",
            "keys": [
                "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a",
                "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf"
            ],
            "openerHash": "9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528",
            "perf": 0
        },
        "certified": True,
        "status": "done",
        "log": "Test - CPU:0.00 % - Mem:0.00 GB - GPU:0.00 % - GPU Mem:0.00 GB; ",
        "permissions": "all",
        "creator": "703433008d3f62dab5ffaccb3c53d723660f5f6cdac3c5dfd26ac88312b5a94e"
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
            "creator": "703433008d3f62dab5ffaccb3c53d723660f5f6cdac3c5dfd26ac88312b5a94e",
            "dataset": {
                "keys": [
                    "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a",
                    "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf"
                ],
                "openerHash": "9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528",
                "perf": 0,
                "worker": "703433008d3f62dab5ffaccb3c53d723660f5f6cdac3c5dfd26ac88312b5a94e"
            },
            "key": "0cd626cf445b1e17f7fb854e696d87db65b460545aab1677920459ae8a774f4f",
            "log": "Test - CPU:0.00 % - Mem:0.00 GB - GPU:0.00 % - GPU Mem:0.00 GB; ",
            "model": {
                "hash": "2bd56e309a7e899027a1e8b3990fd7a69986291043079d836bc2f8bcdb9ec8de",
                "storageAddress": "http://testserver/model/2bd56e309a7e899027a1e8b3990fd7a69986291043079d836bc2f8bcdb9ec8de/file/",
                "traintupleKey": "66caabaf37455cc7af8e89cac37eb0ebfdf73ac7fe4765c644ea6340c2589c0a"
            },
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
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
            "creator": "703433008d3f62dab5ffaccb3c53d723660f5f6cdac3c5dfd26ac88312b5a94e",
            "dataset": {
                "keys": [
                    "bcdda7da240f1de016e5c185d63027ff6536c233f7ed96d086766e99027d4e24",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd",
                "perf": 1,
                "worker": "703433008d3f62dab5ffaccb3c53d723660f5f6cdac3c5dfd26ac88312b5a94e"
            },
            "fltask": "",
            "inModels": None,
            "key": "66caabaf37455cc7af8e89cac37eb0ebfdf73ac7fe4765c644ea6340c2589c0a",
            "log": "Train - CPU:78.04 % - Mem:0.11 GB - GPU:0.00 % - GPU Mem:0.00 GB; ",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "outModel": {
                "hash": "2bd56e309a7e899027a1e8b3990fd7a69986291043079d836bc2f8bcdb9ec8de",
                "storageAddress": "http://testserver/model/2bd56e309a7e899027a1e8b3990fd7a69986291043079d836bc2f8bcdb9ec8de/file/"
            },
            "permissions": "all",
            "rank": 0,
            "status": "done"
        }
    }
]
