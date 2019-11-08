"""
WARNING
=======

DO NOT MANUALLY EDIT THIS FILE!

It is generated using substrapp/tests/generate_assets.py

In order to update this file:
1. start a clean instance of substra
2. run populate.py
3. run substrapp/tests/generate_assets.py
"""

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
            "hash": "e1dec0cdb193497bfad300bcb98b59a05d0055e0d5c9a8347e12f63c2ba8fa35",
            "storageAddress": "http://testserver/objective/1cdafbb018dd195690111d74916b76c96892d897ec3587c814f287946db446c3/metrics/"
        },
        "owner": "MyPeer1MSP",
        "testDataset": None,
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        }
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
            "hash": "e1dec0cdb193497bfad300bcb98b59a05d0055e0d5c9a8347e12f63c2ba8fa35",
            "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
        },
        "owner": "MyPeer1MSP",
        "testDataset": {
            "dataManagerKey": "ce9f292c72e9b82697445117f9c2d1d18ce0f8ed07ff91dadb17d668bddf8932",
            "dataSampleKeys": [
                "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf",
                "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a"
            ],
            "worker": ""
        },
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        }
    }
]

datamanager = [
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
        "owner": "MyPeer1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "type": "Images"
    },
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
        "owner": "MyPeer2MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "type": "Images"
    }
]

algo = [
    {
        "key": "9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d",
        "name": "Logistic regression",
        "content": {
            "hash": "9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d",
            "storageAddress": "http://testserver/algo/9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d/file/"
        },
        "description": {
            "hash": "124a0425b746d7072282d167b53cb6aab3a31bf1946dae89135c15b0126ebec3",
            "storageAddress": "http://testserver/algo/9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d/description/"
        },
        "owner": "MyPeer1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        }
    },
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
        "owner": "MyPeer2MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        }
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
        "owner": "MyPeer2MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        }
    }
]

traintuple = [
    {
        "key": "939e412a4045f17d9c3d7e4b46399afcd78f77647bc74681c259271dc3a3127e",
        "algo": {
            "name": "Neural Network",
            "hash": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f",
            "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/file/"
        },
        "creator": "MyPeer2MSP",
        "dataset": {
            "worker": "MyPeer2MSP",
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 0
        },
        "computePlanID": "",
        "inModels": None,
        "log": "[00-01-0032-7da30ce]",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "e1dec0cdb193497bfad300bcb98b59a05d0055e0d5c9a8347e12f63c2ba8fa35",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outModel": None,
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "rank": 0,
        "status": "failed",
        "tag": "(should fail) My super tag"
    },
    {
        "key": "102d2f2a63ae1dfd118a3349b1f1fe8c8dedf36dfd198597bd7bc03d5367b38b",
        "algo": {
            "name": "Random Forest",
            "hash": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9",
            "storageAddress": "http://testserver/algo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9/file/"
        },
        "creator": "MyPeer2MSP",
        "dataset": {
            "worker": "MyPeer2MSP",
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 0
        },
        "computePlanID": "d4ca4befe79e56b98168b80e17db415f5be8c138ddeb600b6937a3f2aa809de3",
        "inModels": None,
        "log": "[00-01-0032-27dbbe0]",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "e1dec0cdb193497bfad300bcb98b59a05d0055e0d5c9a8347e12f63c2ba8fa35",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outModel": None,
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "rank": 0,
        "status": "failed",
        "tag": "(should fail) My other tag"
    },
    {
        "key": "39005faca3fd168e513c812de144b62fa4ce48df9d0ba1a03c56fae76aebae80",
        "algo": {
            "name": "Logistic regression",
            "hash": "9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d",
            "storageAddress": "http://testserver/algo/9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d/file/"
        },
        "creator": "MyPeer2MSP",
        "dataset": {
            "worker": "MyPeer2MSP",
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 0
        },
        "computePlanID": "",
        "inModels": None,
        "log": "[01-01-0014-b8a6e50]",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "e1dec0cdb193497bfad300bcb98b59a05d0055e0d5c9a8347e12f63c2ba8fa35",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outModel": {
            "hash": "88c1b3c49f54601effbac2027ec5e562c1e6b33b9734fb0c86fa40f4f46745f9",
            "storageAddress": "http://testserver/model/88c1b3c49f54601effbac2027ec5e562c1e6b33b9734fb0c86fa40f4f46745f9/file/"
        },
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        },
        "rank": 0,
        "status": "failed",
        "tag": "(should fail) My other tag"
    },
    {
        "key": "d4ca4befe79e56b98168b80e17db415f5be8c138ddeb600b6937a3f2aa809de3",
        "algo": {
            "name": "Logistic regression",
            "hash": "9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d",
            "storageAddress": "http://testserver/algo/9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d/file/"
        },
        "creator": "MyPeer2MSP",
        "dataset": {
            "worker": "MyPeer2MSP",
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "e3644123451975be20909fcfd9c664a0573d9bfe04c5021625412d78c3536f1c"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 1
        },
        "computePlanID": "d4ca4befe79e56b98168b80e17db415f5be8c138ddeb600b6937a3f2aa809de3",
        "inModels": None,
        "log": "",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "e1dec0cdb193497bfad300bcb98b59a05d0055e0d5c9a8347e12f63c2ba8fa35",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outModel": {
            "hash": "4ae17bbc616c22b6186c2b1a51316f3ccd41c1baf076be218159c5cac3a966f8",
            "storageAddress": "http://testserver/model/4ae17bbc616c22b6186c2b1a51316f3ccd41c1baf076be218159c5cac3a966f8/file/"
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
    }
]

testtuple = [
    {
        "key": "5821c61f285939aec24bc764c5caee81cb9a2e80ff2b8a7c11db0d6d6adfb05b",
        "algo": {
            "name": "Logistic regression",
            "hash": "9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d",
            "storageAddress": "http://testserver/algo/9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d/file/"
        },
        "certified": True,
        "creator": "MyPeer2MSP",
        "dataset": {
            "worker": "MyPeer1MSP",
            "keys": [
                "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a",
                "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf"
            ],
            "openerHash": "ce9f292c72e9b82697445117f9c2d1d18ce0f8ed07ff91dadb17d668bddf8932",
            "perf": 0
        },
        "log": "",
        "traintupleKey": "39005faca3fd168e513c812de144b62fa4ce48df9d0ba1a03c56fae76aebae80",
        "model": {
            "traintupleKey": "39005faca3fd168e513c812de144b62fa4ce48df9d0ba1a03c56fae76aebae80",
            "hash": "88c1b3c49f54601effbac2027ec5e562c1e6b33b9734fb0c86fa40f4f46745f9",
            "storageAddress": "http://testserver/model/88c1b3c49f54601effbac2027ec5e562c1e6b33b9734fb0c86fa40f4f46745f9/file/"
        },
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "e1dec0cdb193497bfad300bcb98b59a05d0055e0d5c9a8347e12f63c2ba8fa35",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "status": "failed",
        "tag": "substra"
    }
]

computeplan = [
    {
        "traintuple": {
            "key": "939e412a4045f17d9c3d7e4b46399afcd78f77647bc74681c259271dc3a3127e",
            "algo": {
                "name": "Neural Network",
                "hash": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f",
                "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/file/"
            },
            "creator": "MyPeer2MSP",
            "dataset": {
                "worker": "MyPeer2MSP",
                "keys": [
                    "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
                "perf": 0
            },
            "computePlanID": "",
            "inModels": None,
            "log": "[00-01-0032-7da30ce]",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "e1dec0cdb193497bfad300bcb98b59a05d0055e0d5c9a8347e12f63c2ba8fa35",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "outModel": None,
            "permissions": {
                "process": {
                    "public": True,
                    "authorizedIDs": []
                }
            },
            "rank": 0,
            "status": "failed",
            "tag": "(should fail) My super tag"
        },
        "testtuple": {
            "key": "",
            "algo": None,
            "certified": False,
            "creator": "",
            "dataset": None,
            "log": "",
            "traintupleKey": "",
            "model": None,
            "objective": None,
            "status": "",
            "tag": ""
        }
    },
    {
        "traintuple": {
            "key": "39005faca3fd168e513c812de144b62fa4ce48df9d0ba1a03c56fae76aebae80",
            "algo": {
                "name": "Logistic regression",
                "hash": "9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d",
                "storageAddress": "http://testserver/algo/9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d/file/"
            },
            "creator": "MyPeer2MSP",
            "dataset": {
                "worker": "MyPeer2MSP",
                "keys": [
                    "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
                "perf": 1
            },
            "computePlanID": "",
            "inModels": None,
            "log": "",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "e1dec0cdb193497bfad300bcb98b59a05d0055e0d5c9a8347e12f63c2ba8fa35",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "outModel": {
                "hash": "88c1b3c49f54601effbac2027ec5e562c1e6b33b9734fb0c86fa40f4f46745f9",
                "storageAddress": "http://testserver/model/88c1b3c49f54601effbac2027ec5e562c1e6b33b9734fb0c86fa40f4f46745f9/file/"
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
            "key": "5821c61f285939aec24bc764c5caee81cb9a2e80ff2b8a7c11db0d6d6adfb05b",
            "algo": {
                "name": "Logistic regression",
                "hash": "9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d",
                "storageAddress": "http://testserver/algo/9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d/file/"
            },
            "certified": True,
            "creator": "MyPeer2MSP",
            "dataset": {
                "worker": "MyPeer1MSP",
                "keys": [
                    "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a",
                    "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf"
                ],
                "openerHash": "ce9f292c72e9b82697445117f9c2d1d18ce0f8ed07ff91dadb17d668bddf8932",
                "perf": 0
            },
            "log": "",
            "traintupleKey": "39005faca3fd168e513c812de144b62fa4ce48df9d0ba1a03c56fae76aebae80",
            "model": {
                "traintupleKey": "39005faca3fd168e513c812de144b62fa4ce48df9d0ba1a03c56fae76aebae80",
                "hash": "88c1b3c49f54601effbac2027ec5e562c1e6b33b9734fb0c86fa40f4f46745f9",
                "storageAddress": "http://testserver/model/88c1b3c49f54601effbac2027ec5e562c1e6b33b9734fb0c86fa40f4f46745f9/file/"
            },
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "e1dec0cdb193497bfad300bcb98b59a05d0055e0d5c9a8347e12f63c2ba8fa35",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "status": "failed",
            "tag": "substra"
        }
    },
{
        "traintuple": {
            "key": "102d2f2a63ae1dfd118a3349b1f1fe8c8dedf36dfd198597bd7bc03d5367b38b",
            "algo": {
                "name": "Random Forest",
                "hash": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9",
                "storageAddress": "http://testserver/algo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9/file/"
            },
            "creator": "MyPeer2MSP",
            "dataset": {
                "worker": "MyPeer2MSP",
                "keys": [
                    "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
                "perf": 0
            },
            "computePlanID": "",
            "inModels": None,
            "log": "[00-01-0032-27dbbe0]",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "e1dec0cdb193497bfad300bcb98b59a05d0055e0d5c9a8347e12f63c2ba8fa35",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "outModel": None,
            "permissions": {
                "process": {
                    "public": True,
                    "authorizedIDs": []
                }
            },
            "rank": 0,
            "status": "failed",
            "tag": "(should fail) My other tag"
        },
        "testtuple": {
            "key": "",
            "algo": None,
            "certified": False,
            "creator": "",
            "dataset": None,
            "log": "",
            "traintupleKey": "",
            "model": None,
            "objective": None,
            "status": "",
            "tag": ""
        }
    },
    {
        "traintuple": {
            "key": "d4ca4befe79e56b98168b80e17db415f5be8c138ddeb600b6937a3f2aa809de3",
            "algo": {
                "name": "Logistic regression",
                "hash": "9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d",
                "storageAddress": "http://testserver/algo/9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d/file/"
            },
            "creator": "MyPeer2MSP",
            "dataset": {
                "worker": "MyPeer2MSP",
                "keys": [
                    "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                    "e3644123451975be20909fcfd9c664a0573d9bfe04c5021625412d78c3536f1c"
                ],
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
                "perf": 1
            },
            "computePlanID": "d4ca4befe79e56b98168b80e17db415f5be8c138ddeb600b6937a3f2aa809de3",
            "inModels": None,
            "log": "",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "e1dec0cdb193497bfad300bcb98b59a05d0055e0d5c9a8347e12f63c2ba8fa35",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "outModel": {
                "hash": "4ae17bbc616c22b6186c2b1a51316f3ccd41c1baf076be218159c5cac3a966f8",
                "storageAddress": "http://testserver/model/4ae17bbc616c22b6186c2b1a51316f3ccd41c1baf076be218159c5cac3a966f8/file/"
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
            "key": "",
            "algo": None,
            "certified": False,
            "creator": "",
            "dataset": None,
            "log": "",
            "traintupleKey": "",
            "model": None,
            "objective": None,
            "status": "",
            "tag": ""
        }
    }
]
