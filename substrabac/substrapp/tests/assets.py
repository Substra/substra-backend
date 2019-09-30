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
            "hash": "501b94306d9c65650273629d0f5e8177043dc3cc93ea309263fcc52f1eb010e0",
            "storageAddress": "http://testserver/objective/1cdafbb018dd195690111d74916b76c96892d897ec3587c814f287946db446c3/metrics/"
        },
        "owner": "owkinMSP",
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
            "hash": "501b94306d9c65650273629d0f5e8177043dc3cc93ea309263fcc52f1eb010e0",
            "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
        },
        "owner": "owkinMSP",
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
            "hash": "15863c2af1fcfee9ca6f61f04be8a0eaaf6a45e4d50c421788d450d198e580f1",
            "storageAddress": "http://testserver/data_manager/8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca/description/"
        },
        "key": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
        "name": "ISIC 2018",
        "opener": {
            "hash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "storageAddress": "http://testserver/data_manager/8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca/opener/"
        },
        "owner": "chu-nantesMSP",
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
            "hash": "258bef187a166b3fef5cb86e68c8f7e154c283a148cd5bc344fec7e698821ad3",
            "storageAddress": "http://testserver/data_manager/ce9f292c72e9b82697445117f9c2d1d18ce0f8ed07ff91dadb17d668bddf8932/description/"
        },
        "key": "ce9f292c72e9b82697445117f9c2d1d18ce0f8ed07ff91dadb17d668bddf8932",
        "name": "Simplified ISIC 2018",
        "opener": {
            "hash": "ce9f292c72e9b82697445117f9c2d1d18ce0f8ed07ff91dadb17d668bddf8932",
            "storageAddress": "http://testserver/data_manager/ce9f292c72e9b82697445117f9c2d1d18ce0f8ed07ff91dadb17d668bddf8932/opener/"
        },
        "owner": "owkinMSP",
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
        "owner": "chu-nantesMSP",
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
        "owner": "chu-nantesMSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        }
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
        "owner": "owkinMSP",
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
        "key": "0cdf5520e2b5d4242bd503791a2da3afaeaf7f45b84b388667367b7e4df7c3d3",
        "algo": {
            "name": "Neural Network",
            "hash": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f",
            "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/file/"
        },
        "creator": "chu-nantesMSP",
        "dataset": {
            "worker": "chu-nantesMSP",
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 0
        },
        "computePlanID": "",
        "inModels": None,
        "log": "[01-01-0165-e17cc59]",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "501b94306d9c65650273629d0f5e8177043dc3cc93ea309263fcc52f1eb010e0",
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
        "tag": "My super tag"
    },
    {
        "key": "0bd1a982d5d26699a2c32fe8ec72d9debb0af017a91a45c98fe1f8bf784b0b87",
        "algo": {
            "name": "Logistic regression",
            "hash": "7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5",
            "storageAddress": "http://testserver/algo/7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5/file/"
        },
        "creator": "chu-nantesMSP",
        "dataset": {
            "worker": "chu-nantesMSP",
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
                "hash": "501b94306d9c65650273629d0f5e8177043dc3cc93ea309263fcc52f1eb010e0",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outModel": {
            "hash": "4d79c29495e1d6bb7bbe920c633eae328ab25e79a8e77e37a2e0315839fc6d8b",
            "storageAddress": "http://testserver/model/4d79c29495e1d6bb7bbe920c633eae328ab25e79a8e77e37a2e0315839fc6d8b/file/"
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
        "key": "94be807e307b3c14e3bee15478ac466ac1fbc373cd207a0c4db9456c971e518a",
        "algo": {
            "name": "Logistic regression",
            "hash": "7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5",
            "storageAddress": "http://testserver/algo/7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5/file/"
        },
        "creator": "chu-nantesMSP",
        "dataset": {
            "worker": "chu-nantesMSP",
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "e3644123451975be20909fcfd9c664a0573d9bfe04c5021625412d78c3536f1c"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 1
        },
        "computePlanID": "94be807e307b3c14e3bee15478ac466ac1fbc373cd207a0c4db9456c971e518a",
        "inModels": None,
        "log": "",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "501b94306d9c65650273629d0f5e8177043dc3cc93ea309263fcc52f1eb010e0",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outModel": {
            "hash": "77f61ca2a815e04487f6c212f7e9342437c3c30e3c2dad56e994f4d802607193",
            "storageAddress": "http://testserver/model/77f61ca2a815e04487f6c212f7e9342437c3c30e3c2dad56e994f4d802607193/file/"
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
        "key": "dd80853c84f752b69fb0738f368d32a56a16e072e81f1c9fd6e781cc27ca80b3",
        "algo": {
            "name": "Random Forest",
            "hash": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9",
            "storageAddress": "http://testserver/algo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9/file/"
        },
        "creator": "chu-nantesMSP",
        "dataset": {
            "worker": "chu-nantesMSP",
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 0
        },
        "computePlanID": "",
        "inModels": None,
        "log": "[01-01-0165-32eaa7e]",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "501b94306d9c65650273629d0f5e8177043dc3cc93ea309263fcc52f1eb010e0",
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
        "tag": ""
    }
]

testtuple = [
    {
        "key": "2672e448f9944748664a0b5dceb335de8db7f2646e9da2a836d8ebbec2c3fd4c",
        "algo": {
            "name": "Logistic regression",
            "hash": "7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5",
            "storageAddress": "http://testserver/algo/7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5/file/"
        },
        "certified": True,
        "creator": "chu-nantesMSP",
        "dataset": {
            "worker": "owkinMSP",
            "keys": [
                "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a",
                "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf"
            ],
            "openerHash": "ce9f292c72e9b82697445117f9c2d1d18ce0f8ed07ff91dadb17d668bddf8932",
            "perf": 0
        },
        "log": "",
        "model": {
            "traintupleKey": "0bd1a982d5d26699a2c32fe8ec72d9debb0af017a91a45c98fe1f8bf784b0b87",
            "hash": "4d79c29495e1d6bb7bbe920c633eae328ab25e79a8e77e37a2e0315839fc6d8b",
            "storageAddress": "http://testserver/model/4d79c29495e1d6bb7bbe920c633eae328ab25e79a8e77e37a2e0315839fc6d8b/file/"
        },
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "501b94306d9c65650273629d0f5e8177043dc3cc93ea309263fcc52f1eb010e0",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "status": "done",
        "tag": "substra"
    }
]

model = [
    {
        "traintuple": {
            "key": "0cdf5520e2b5d4242bd503791a2da3afaeaf7f45b84b388667367b7e4df7c3d3",
            "algo": {
                "name": "Neural Network",
                "hash": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f",
                "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/file/"
            },
            "creator": "chu-nantesMSP",
            "dataset": {
                "worker": "chu-nantesMSP",
                "keys": [
                    "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
                "perf": 0
            },
            "computePlanID": "",
            "inModels": None,
            "log": "[01-01-0165-e17cc59]",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "501b94306d9c65650273629d0f5e8177043dc3cc93ea309263fcc52f1eb010e0",
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
            "status": "",
            "tag": ""
        }
    },
    {
        "traintuple": {
            "key": "0bd1a982d5d26699a2c32fe8ec72d9debb0af017a91a45c98fe1f8bf784b0b87",
            "algo": {
                "name": "Logistic regression",
                "hash": "7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5",
                "storageAddress": "http://testserver/algo/7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5/file/"
            },
            "creator": "chu-nantesMSP",
            "dataset": {
                "worker": "chu-nantesMSP",
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
                    "hash": "501b94306d9c65650273629d0f5e8177043dc3cc93ea309263fcc52f1eb010e0",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "outModel": {
                "hash": "4d79c29495e1d6bb7bbe920c633eae328ab25e79a8e77e37a2e0315839fc6d8b",
                "storageAddress": "http://testserver/model/4d79c29495e1d6bb7bbe920c633eae328ab25e79a8e77e37a2e0315839fc6d8b/file/"
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
        "testtuple": {
            "key": "2672e448f9944748664a0b5dceb335de8db7f2646e9da2a836d8ebbec2c3fd4c",
            "algo": {
                "name": "Logistic regression",
                "hash": "7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5",
                "storageAddress": "http://testserver/algo/7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5/file/"
            },
            "certified": True,
            "creator": "chu-nantesMSP",
            "dataset": {
                "worker": "owkinMSP",
                "keys": [
                    "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a",
                    "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf"
                ],
                "openerHash": "ce9f292c72e9b82697445117f9c2d1d18ce0f8ed07ff91dadb17d668bddf8932",
                "perf": 0
            },
            "log": "",
            "model": {
                "traintupleKey": "0bd1a982d5d26699a2c32fe8ec72d9debb0af017a91a45c98fe1f8bf784b0b87",
                "hash": "4d79c29495e1d6bb7bbe920c633eae328ab25e79a8e77e37a2e0315839fc6d8b",
                "storageAddress": "http://testserver/model/4d79c29495e1d6bb7bbe920c633eae328ab25e79a8e77e37a2e0315839fc6d8b/file/"
            },
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "501b94306d9c65650273629d0f5e8177043dc3cc93ea309263fcc52f1eb010e0",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "status": "done",
            "tag": "substra"
        }
    },
    {
        "traintuple": {
            "key": "94be807e307b3c14e3bee15478ac466ac1fbc373cd207a0c4db9456c971e518a",
            "algo": {
                "name": "Logistic regression",
                "hash": "7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5",
                "storageAddress": "http://testserver/algo/7c9f9799bf64c10002381583a9ffc535bc3f4bf14d6f0c614d3f6f868f72a9d5/file/"
            },
            "creator": "chu-nantesMSP",
            "dataset": {
                "worker": "chu-nantesMSP",
                "keys": [
                    "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                    "e3644123451975be20909fcfd9c664a0573d9bfe04c5021625412d78c3536f1c"
                ],
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
                "perf": 1
            },
            "computePlanID": "94be807e307b3c14e3bee15478ac466ac1fbc373cd207a0c4db9456c971e518a",
            "inModels": None,
            "log": "",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "501b94306d9c65650273629d0f5e8177043dc3cc93ea309263fcc52f1eb010e0",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "outModel": {
                "hash": "77f61ca2a815e04487f6c212f7e9342437c3c30e3c2dad56e994f4d802607193",
                "storageAddress": "http://testserver/model/77f61ca2a815e04487f6c212f7e9342437c3c30e3c2dad56e994f4d802607193/file/"
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
            "model": None,
            "objective": None,
            "status": "",
            "tag": ""
        }
    },
    {
        "traintuple": {
            "key": "dd80853c84f752b69fb0738f368d32a56a16e072e81f1c9fd6e781cc27ca80b3",
            "algo": {
                "name": "Random Forest",
                "hash": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9",
                "storageAddress": "http://testserver/algo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9/file/"
            },
            "creator": "chu-nantesMSP",
            "dataset": {
                "worker": "chu-nantesMSP",
                "keys": [
                    "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
                "perf": 0
            },
            "computePlanID": "",
            "inModels": None,
            "log": "[01-01-0165-32eaa7e]",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "501b94306d9c65650273629d0f5e8177043dc3cc93ea309263fcc52f1eb010e0",
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
            "status": "",
            "tag": ""
        }
    }
]

