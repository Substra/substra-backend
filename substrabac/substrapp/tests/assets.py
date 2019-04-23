objective = [
    {
        "key": "1cdafbb018dd195690111d74916b76c96892d897ec3587c814f287946db446c3",
        "name": "Skin Lesion Classification Objective",
        "description": {
            "hash": "1cdafbb018dd195690111d74916b76c96892d897ec3587c814f287946db446c3",
            "storageAddress": "http://testserver/objective/1cdafbb018dd195690111d74916b76c96892d897ec3587c814f287946db446c3/description/"
        },
        "metrics": {
            "name": "macro-average recall",
            "hash": "0bc732c26bafdc41321c2bffd35b6835aa35f7371a4eb02994642c2c3a688f60",
            "storageAddress": "http://testserver/objective/1cdafbb018dd195690111d74916b76c96892d897ec3587c814f287946db446c3/metrics/"
        },
        "owner": "506fb2dd5891731166847208f7a7d1b17371c577af72f26286bb81c730c18a18",
        "testDataset": None,
        "permissions": "all"
    },
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
        "owner": "506fb2dd5891731166847208f7a7d1b17371c577af72f26286bb81c730c18a18",
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
            "hash": "258bef187a166b3fef5cb86e68c8f7e154c283a148cd5bc344fec7e698821ad3",
            "storageAddress": "http://testserver/data_manager/9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528/description/"
        },
        "key": "9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528",
        "name": "Simplified ISIC 2018",
        "opener": {
            "hash": "9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528",
            "storageAddress": "http://testserver/data_manager/9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528/opener/"
        },
        "owner": "506fb2dd5891731166847208f7a7d1b17371c577af72f26286bb81c730c18a18",
        "permissions": "all",
        "type": "Images"
    },
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
        "owner": "7e710b07840296d00cb5a12c60e5c2f4dfeaae71064dd257f9875ed4d7637d22",
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
        "owner": "7e710b07840296d00cb5a12c60e5c2f4dfeaae71064dd257f9875ed4d7637d22",
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
        "owner": "7e710b07840296d00cb5a12c60e5c2f4dfeaae71064dd257f9875ed4d7637d22",
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
        "owner": "7e710b07840296d00cb5a12c60e5c2f4dfeaae71064dd257f9875ed4d7637d22",
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
        "creator": "7e710b07840296d00cb5a12c60e5c2f4dfeaae71064dd257f9875ed4d7637d22",
        "dataset": {
            "keys": [
                "bcdda7da240f1de016e5c185d63027ff6536c233f7ed96d086766e99027d4e24",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd",
            "perf": 0,
            "worker": "7e710b07840296d00cb5a12c60e5c2f4dfeaae71064dd257f9875ed4d7637d22"
        },
        "fltask": "",
        "inModels": None,
        "key": "1a585c39a427b14e96388f2fb2acd10bc0b26560022a40cb371cbcc55b3cafc7",
        "log": "[00-01-0032-45bad7f]",
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
        "status": "failed",
        "tag": "My super tag"
    },
    {
        "algo": {
            "hash": "da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b",
            "name": "Logistic regression",
            "storageAddress": "http://testserver/algo/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/file/"
        },
        "creator": "7e710b07840296d00cb5a12c60e5c2f4dfeaae71064dd257f9875ed4d7637d22",
        "dataset": {
            "keys": [
                "bcdda7da240f1de016e5c185d63027ff6536c233f7ed96d086766e99027d4e24",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd",
            "perf": 1,
            "worker": "7e710b07840296d00cb5a12c60e5c2f4dfeaae71064dd257f9875ed4d7637d22"
        },
        "fltask": "",
        "inModels": None,
        "key": "1ef64eb72db5d8d8aed6a35582e83487db5d085215678561283c54abace649a1",
        "log": "Train - CPU:77.60 % - Mem:0.11 GB - GPU:0.00 % - GPU Mem:0.00 GB; ",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outModel": {
            "hash": "e87a2d0a70a084acebf038b95790850cc72a96dff684f07ea1dc6a58dd03882b",
            "storageAddress": "http://testserver/model/e87a2d0a70a084acebf038b95790850cc72a96dff684f07ea1dc6a58dd03882b/file/"
        },
        "permissions": "all",
        "rank": 0,
        "status": "done",
        "tag": "substra"
    },
    {
        "algo": {
            "hash": "f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284",
            "name": "Random Forest",
            "storageAddress": "http://testserver/algo/f2d9fd38e25cd975c49f3ce7e6739846585e89635a86689b5db42ab2c0c57284/file/"
        },
        "creator": "7e710b07840296d00cb5a12c60e5c2f4dfeaae71064dd257f9875ed4d7637d22",
        "dataset": {
            "keys": [
                "bcdda7da240f1de016e5c185d63027ff6536c233f7ed96d086766e99027d4e24",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd",
            "perf": 0,
            "worker": "7e710b07840296d00cb5a12c60e5c2f4dfeaae71064dd257f9875ed4d7637d22"
        },
        "fltask": "",
        "inModels": None,
        "key": "9271dbc9d629c5d3bccd4c6f269f54e0d253fb5c53d3de958159605778b3de29",
        "log": "[00-01-0032-899a79c]",
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
        "status": "failed",
        "tag": ""
    }
]

testtuple = [
    {
        "key": "cc0c0465c6aff2fd195bcc8e2ad45379f991a141224340f984d61556e6bfd09c",
        "algo": {
            "name": "Logistic regression",
            "hash": "da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b",
            "storageAddress": "http://testserver/algo/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/file/"
        },
        "certified": True,
        "creator": "7e710b07840296d00cb5a12c60e5c2f4dfeaae71064dd257f9875ed4d7637d22",
        "dataset": {
            "worker": "506fb2dd5891731166847208f7a7d1b17371c577af72f26286bb81c730c18a18",
            "keys": [
                "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a",
                "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf"
            ],
            "openerHash": "9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528",
            "perf": 0
        },
        "log": "Test - CPU:0.00 % - Mem:0.00 GB - GPU:0.00 % - GPU Mem:0.00 GB; ",
        "model": {
            "traintupleKey": "1ef64eb72db5d8d8aed6a35582e83487db5d085215678561283c54abace649a1",
            "hash": "e87a2d0a70a084acebf038b95790850cc72a96dff684f07ea1dc6a58dd03882b",
            "storageAddress": "http://testserver/model/e87a2d0a70a084acebf038b95790850cc72a96dff684f07ea1dc6a58dd03882b/file/"
        },
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "permissions": "all",
        "status": "done",
        "tag": ""
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
            "creator": "7e710b07840296d00cb5a12c60e5c2f4dfeaae71064dd257f9875ed4d7637d22",
            "dataset": {
                "keys": [
                    "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a",
                    "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf"
                ],
                "openerHash": "9a832ed6cee6acf7e33c3acffbc89cebf10ef503b690711bdee048b873daf528",
                "perf": 0,
                "worker": "506fb2dd5891731166847208f7a7d1b17371c577af72f26286bb81c730c18a18"
            },
            "key": "cc0c0465c6aff2fd195bcc8e2ad45379f991a141224340f984d61556e6bfd09c",
            "log": "Test - CPU:0.00 % - Mem:0.00 GB - GPU:0.00 % - GPU Mem:0.00 GB; ",
            "model": {
                "hash": "e87a2d0a70a084acebf038b95790850cc72a96dff684f07ea1dc6a58dd03882b",
                "storageAddress": "http://testserver/model/e87a2d0a70a084acebf038b95790850cc72a96dff684f07ea1dc6a58dd03882b/file/",
                "traintupleKey": "1ef64eb72db5d8d8aed6a35582e83487db5d085215678561283c54abace649a1"
            },
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "permissions": "all",
            "status": "done",
            "tag": ""
        },
        "traintuple": {
            "algo": {
                "hash": "da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b",
                "name": "Logistic regression",
                "storageAddress": "http://testserver/algo/da58a7a29b549f2fe5f009fb51cce6b28ca184ec641a0c1db075729bb266549b/file/"
            },
            "creator": "7e710b07840296d00cb5a12c60e5c2f4dfeaae71064dd257f9875ed4d7637d22",
            "dataset": {
                "keys": [
                    "bcdda7da240f1de016e5c185d63027ff6536c233f7ed96d086766e99027d4e24",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "59300f1fec4f5cdd3a236c7260ed72bdd24691efdec63b7910ea84136123cecd",
                "perf": 1,
                "worker": "7e710b07840296d00cb5a12c60e5c2f4dfeaae71064dd257f9875ed4d7637d22"
            },
            "fltask": "",
            "inModels": None,
            "key": "1ef64eb72db5d8d8aed6a35582e83487db5d085215678561283c54abace649a1",
            "log": "Train - CPU:77.60 % - Mem:0.11 GB - GPU:0.00 % - GPU Mem:0.00 GB; ",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "750f622262854341bd44f55c1018949e9c119606ef5068bd7d137040a482a756",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "outModel": {
                "hash": "e87a2d0a70a084acebf038b95790850cc72a96dff684f07ea1dc6a58dd03882b",
                "storageAddress": "http://testserver/model/e87a2d0a70a084acebf038b95790850cc72a96dff684f07ea1dc6a58dd03882b/file/"
            },
            "permissions": "all",
            "rank": 0,
            "status": "done",
            "tag": "substra"
        }
    }
]

