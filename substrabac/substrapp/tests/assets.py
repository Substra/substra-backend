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
            "hash": "c42dca31fbc2ebb5705643e3bb6ee666bbfd956de13dd03727f825ad8445b4d7",
            "storageAddress": "http://testserver/objective/1cdafbb018dd195690111d74916b76c96892d897ec3587c814f287946db446c3/metrics/"
        },
        "owner": "f745cba1182632bc7a0bed0bd9dac12abc33ed4120d840665c7405fa2719dc1e",
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
            "hash": "c42dca31fbc2ebb5705643e3bb6ee666bbfd956de13dd03727f825ad8445b4d7",
            "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
        },
        "owner": "f745cba1182632bc7a0bed0bd9dac12abc33ed4120d840665c7405fa2719dc1e",
        "testDataset": {
            "dataManagerKey": "ce9f292c72e9b82697445117f9c2d1d18ce0f8ed07ff91dadb17d668bddf8932",
            "dataSampleKeys": [
                "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf",
                "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a"
            ],
            "worker": ""
        },
        "permissions": "all"
    }
]

datamanager = [
    {
        "objectiveKey": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
        "description": {
            "hash": "15863c2af1fcfee9ca6f61f04be8a0eaaf6a45e4d50c421788d450d198e580f1",
            "storageAddress": "http://testserver/data_manager/8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca/description/"
        },
        "key": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
        "name": "ISIC 2018",
        "opener": {
            "hash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "storageAddress": "http://testserver/data_manager/8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca/opener/"
        },
        "owner": "9d62c8eb34f3cb04c15e1d893afd3639dbc6a2491f5115856a98c10c256a034e",
        "permissions": "all",
        "type": "Images"
    },
    {
        "objectiveKey": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
        "description": {
            "hash": "258bef187a166b3fef5cb86e68c8f7e154c283a148cd5bc344fec7e698821ad3",
            "storageAddress": "http://testserver/data_manager/ce9f292c72e9b82697445117f9c2d1d18ce0f8ed07ff91dadb17d668bddf8932/description/"
        },
        "key": "ce9f292c72e9b82697445117f9c2d1d18ce0f8ed07ff91dadb17d668bddf8932",
        "name": "Simplified ISIC 2018",
        "opener": {
            "hash": "ce9f292c72e9b82697445117f9c2d1d18ce0f8ed07ff91dadb17d668bddf8932",
            "storageAddress": "http://testserver/data_manager/ce9f292c72e9b82697445117f9c2d1d18ce0f8ed07ff91dadb17d668bddf8932/opener/"
        },
        "owner": "f745cba1182632bc7a0bed0bd9dac12abc33ed4120d840665c7405fa2719dc1e",
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
        "owner": "9d62c8eb34f3cb04c15e1d893afd3639dbc6a2491f5115856a98c10c256a034e",
        "permissions": "all"
    },
    {
        "key": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9",
        "name": "Random Forest",
        "content": {
            "hash": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9",
            "storageAddress": "http://testserver/algo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9/file/"
        },
        "description": {
            "hash": "4acea40c4b51996c88ef279c5c9aa41ab77b97d38c5ca167e978a98b2e402675",
            "storageAddress": "http://testserver/algo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9/description/"
        },
        "owner": "9d62c8eb34f3cb04c15e1d893afd3639dbc6a2491f5115856a98c10c256a034e",
        "permissions": "all"
    },
    {
        "key": "7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5",
        "name": "Logistic regression",
        "content": {
            "hash": "7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5",
            "storageAddress": "http://testserver/algo/7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5/file/"
        },
        "description": {
            "hash": "124a0425b746d7072282d167b53cb6aab3a31bf1946dae89135c15b0126ebec3",
            "storageAddress": "http://testserver/algo/7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5/description/"
        },
        "owner": "f745cba1182632bc7a0bed0bd9dac12abc33ed4120d840665c7405fa2719dc1e",
        "permissions": "all"
    }
]

traintuple = [
    {
        "key": "8e8c724a3308b81b01f69ea96da80bac9cd5c2f31d08f54531da17aa1a8cca7e",
        "algo": {
            "name": "Neural Network",
            "hash": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f",
            "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/file/"
        },
        "creator": "9d62c8eb34f3cb04c15e1d893afd3639dbc6a2491f5115856a98c10c256a034e",
        "dataset": {
            "worker": "9d62c8eb34f3cb04c15e1d893afd3639dbc6a2491f5115856a98c10c256a034e",
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 0
        },
        "compute_plan_id": "",
        "inModels": None,
        "log": "[00-01-0032-8a01ed9]",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "c42dca31fbc2ebb5705643e3bb6ee666bbfd956de13dd03727f825ad8445b4d7",
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
        "key": "00227da7d49a20c228e0c10a3283891b9c0ded90685959cba55f0ba3f38123bb",
        "algo": {
            "name": "Logistic regression",
            "hash": "7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5",
            "storageAddress": "http://testserver/algo/7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5/file/"
        },
        "creator": "9d62c8eb34f3cb04c15e1d893afd3639dbc6a2491f5115856a98c10c256a034e",
        "dataset": {
            "worker": "9d62c8eb34f3cb04c15e1d893afd3639dbc6a2491f5115856a98c10c256a034e",
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 1
        },
        "compute_plan_id": "",
        "inModels": None,
        "log": "Train - CPU:268.84 % - Mem:0.11 GB - GPU:0.00 % - GPU Mem:0.00 GB;",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "c42dca31fbc2ebb5705643e3bb6ee666bbfd956de13dd03727f825ad8445b4d7",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outModel": {
            "hash": "a2a21351da7665e0fc37a2173e1f33fb9e217e9c46c279ec9a1895e82ece6717",
            "storageAddress": "http://testserver/model/a2a21351da7665e0fc37a2173e1f33fb9e217e9c46c279ec9a1895e82ece6717/file/"
        },
        "permissions": "all",
        "rank": 0,
        "status": "done",
        "tag": "substra"
    },
    {
        "key": "6ac5dc6f51bf793248b18906171f3133cf24eb04e2fd0bafa3f86ff9b518c886",
        "algo": {
            "name": "Random Forest",
            "hash": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9",
            "storageAddress": "http://testserver/algo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9/file/"
        },
        "creator": "9d62c8eb34f3cb04c15e1d893afd3639dbc6a2491f5115856a98c10c256a034e",
        "dataset": {
            "worker": "9d62c8eb34f3cb04c15e1d893afd3639dbc6a2491f5115856a98c10c256a034e",
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 0
        },
        "compute_plan_id": "",
        "inModels": None,
        "log": "[00-01-0032-4647065]",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "c42dca31fbc2ebb5705643e3bb6ee666bbfd956de13dd03727f825ad8445b4d7",
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
        "key": "8fbcd8f301447c73e7cfd0afac9dca9300d6fc948060af588de02c8ca946ffc0",
        "algo": {
            "name": "Logistic regression",
            "hash": "7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5",
            "storageAddress": "http://testserver/algo/7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5/file/"
        },
        "certified": True,
        "creator": "9d62c8eb34f3cb04c15e1d893afd3639dbc6a2491f5115856a98c10c256a034e",
        "dataset": {
            "worker": "f745cba1182632bc7a0bed0bd9dac12abc33ed4120d840665c7405fa2719dc1e",
            "keys": [
                "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a",
                "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf"
            ],
            "openerHash": "ce9f292c72e9b82697445117f9c2d1d18ce0f8ed07ff91dadb17d668bddf8932",
            "perf": 0
        },
        "log": "Test - CPU:0.00 % - Mem:0.00 GB - GPU:0.00 % - GPU Mem:0.00 GB;",
        "model": {
            "traintupleKey": "00227da7d49a20c228e0c10a3283891b9c0ded90685959cba55f0ba3f38123bb",
            "hash": "a2a21351da7665e0fc37a2173e1f33fb9e217e9c46c279ec9a1895e82ece6717",
            "storageAddress": "http://testserver/model/a2a21351da7665e0fc37a2173e1f33fb9e217e9c46c279ec9a1895e82ece6717/file/"
        },
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "c42dca31fbc2ebb5705643e3bb6ee666bbfd956de13dd03727f825ad8445b4d7",
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
        "traintuple": {
            "key": "8e8c724a3308b81b01f69ea96da80bac9cd5c2f31d08f54531da17aa1a8cca7e",
            "algo": {
                "name": "Neural Network",
                "hash": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f",
                "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/file/"
            },
            "creator": "9d62c8eb34f3cb04c15e1d893afd3639dbc6a2491f5115856a98c10c256a034e",
            "dataset": {
                "worker": "9d62c8eb34f3cb04c15e1d893afd3639dbc6a2491f5115856a98c10c256a034e",
                "keys": [
                    "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
                "perf": 0
            },
            "compute_plan_id": "",
            "inModels": None,
            "log": "[00-01-0032-8a01ed9]",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "c42dca31fbc2ebb5705643e3bb6ee666bbfd956de13dd03727f825ad8445b4d7",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "outModel": None,
            "permissions": "all",
            "rank": 0,
            "status": "failed",
            "tag": "My super tag"
        },
        "testtuple": {
            "key": "",
            "algo": None,
            "certified": False,
            "creator": "",
            "dataset": None,
            "log": "",
            "model": None,
            "objective": None,
            "permissions": "",
            "status": "",
            "tag": ""
        }
    },
    {
        "traintuple": {
            "key": "00227da7d49a20c228e0c10a3283891b9c0ded90685959cba55f0ba3f38123bb",
            "algo": {
                "name": "Logistic regression",
                "hash": "7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5",
                "storageAddress": "http://testserver/algo/7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5/file/"
            },
            "creator": "9d62c8eb34f3cb04c15e1d893afd3639dbc6a2491f5115856a98c10c256a034e",
            "dataset": {
                "worker": "9d62c8eb34f3cb04c15e1d893afd3639dbc6a2491f5115856a98c10c256a034e",
                "keys": [
                    "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
                "perf": 1
            },
            "compute_plan_id": "",
            "inModels": None,
            "log": "Train - CPU:268.84 % - Mem:0.11 GB - GPU:0.00 % - GPU Mem:0.00 GB;",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "c42dca31fbc2ebb5705643e3bb6ee666bbfd956de13dd03727f825ad8445b4d7",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "outModel": {
                "hash": "a2a21351da7665e0fc37a2173e1f33fb9e217e9c46c279ec9a1895e82ece6717",
                "storageAddress": "http://testserver/model/a2a21351da7665e0fc37a2173e1f33fb9e217e9c46c279ec9a1895e82ece6717/file/"
            },
            "permissions": "all",
            "rank": 0,
            "status": "done",
            "tag": "substra"
        },
        "testtuple": {
            "key": "8fbcd8f301447c73e7cfd0afac9dca9300d6fc948060af588de02c8ca946ffc0",
            "algo": {
                "name": "Logistic regression",
                "hash": "7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5",
                "storageAddress": "http://testserver/algo/7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5/file/"
            },
            "certified": True,
            "creator": "9d62c8eb34f3cb04c15e1d893afd3639dbc6a2491f5115856a98c10c256a034e",
            "dataset": {
                "worker": "f745cba1182632bc7a0bed0bd9dac12abc33ed4120d840665c7405fa2719dc1e",
                "keys": [
                    "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a",
                    "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf"
                ],
                "openerHash": "ce9f292c72e9b82697445117f9c2d1d18ce0f8ed07ff91dadb17d668bddf8932",
                "perf": 0
            },
            "log": "Test - CPU:0.00 % - Mem:0.00 GB - GPU:0.00 % - GPU Mem:0.00 GB;",
            "model": {
                "traintupleKey": "00227da7d49a20c228e0c10a3283891b9c0ded90685959cba55f0ba3f38123bb",
                "hash": "a2a21351da7665e0fc37a2173e1f33fb9e217e9c46c279ec9a1895e82ece6717",
                "storageAddress": "http://testserver/model/a2a21351da7665e0fc37a2173e1f33fb9e217e9c46c279ec9a1895e82ece6717/file/"
            },
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "c42dca31fbc2ebb5705643e3bb6ee666bbfd956de13dd03727f825ad8445b4d7",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "permissions": "all",
            "status": "done",
            "tag": ""
        }
    },
    {
        "traintuple": {
            "key": "6ac5dc6f51bf793248b18906171f3133cf24eb04e2fd0bafa3f86ff9b518c886",
            "algo": {
                "name": "Random Forest",
                "hash": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9",
                "storageAddress": "http://testserver/algo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9/file/"
            },
            "creator": "9d62c8eb34f3cb04c15e1d893afd3639dbc6a2491f5115856a98c10c256a034e",
            "dataset": {
                "worker": "9d62c8eb34f3cb04c15e1d893afd3639dbc6a2491f5115856a98c10c256a034e",
                "keys": [
                    "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
                "perf": 0
            },
            "compute_plan_id": "",
            "inModels": None,
            "log": "[00-01-0032-4647065]",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "c42dca31fbc2ebb5705643e3bb6ee666bbfd956de13dd03727f825ad8445b4d7",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "outModel": None,
            "permissions": "all",
            "rank": 0,
            "status": "failed",
            "tag": ""
        },
        "testtuple": {
            "key": "",
            "algo": None,
            "certified": False,
            "creator": "",
            "dataset": None,
            "log": "",
            "model": None,
            "objective": None,
            "permissions": "",
            "status": "",
            "tag": ""
        }
    }
]

