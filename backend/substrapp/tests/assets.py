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
            "hash": "e5762042461c355761dd8986b510ea23494d5638a671370dabbf0ac73f8a3208",
            "storageAddress": "http://testserver/objective/1cdafbb018dd195690111d74916b76c96892d897ec3587c814f287946db446c3/metrics/"
        },
        "owner": "MyOrg1MSP",
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
            "hash": "e5762042461c355761dd8986b510ea23494d5638a671370dabbf0ac73f8a3208",
            "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
        },
        "owner": "MyOrg1MSP",
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
        "owner": "MyOrg1MSP",
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
        "owner": "MyOrg2MSP",
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
        "owner": "MyOrg1MSP",
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
        "owner": "MyOrg2MSP",
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
        "owner": "MyOrg2MSP",
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
        "key": "c1d77d8e53f048b60863a1c453c60392e3f2b7b38dd0853f9b9664a5cef1c7cc",
        "algo": {
            "name": "Neural Network",
            "hash": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f",
            "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/file/"
        },
        "creator": "MyOrg2MSP",
        "dataset": {
            "worker": "MyOrg2MSP",
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 0
        },
        "computePlanID": "",
        "inModels": None,
        "log": "[01-01-0014-f7f130b]",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "e5762042461c355761dd8986b510ea23494d5638a671370dabbf0ac73f8a3208",
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
        "key": "a55fb929e12bca0be8e7d6db58bc7f5b6d2134c7c36d29961729da54d383dc01",
        "algo": {
            "name": "Random Forest",
            "hash": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9",
            "storageAddress": "http://testserver/algo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9/file/"
        },
        "creator": "MyOrg2MSP",
        "dataset": {
            "worker": "MyOrg2MSP",
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 0
        },
        "computePlanID": "",
        "inModels": None,
        "log": "[01-01-0014-01b28b3]",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "e5762042461c355761dd8986b510ea23494d5638a671370dabbf0ac73f8a3208",
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
        "key": "d7e429016148abfac682ec6a183b7883ccb96cd375bb3c7f5d3c35816c04f7d6",
        "algo": {
            "name": "Logistic regression",
            "hash": "9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d",
            "storageAddress": "http://testserver/algo/9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d/file/"
        },
        "creator": "MyOrg2MSP",
        "dataset": {
            "worker": "MyOrg2MSP",
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
                "hash": "e5762042461c355761dd8986b510ea23494d5638a671370dabbf0ac73f8a3208",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outModel": {
            "hash": "53fbedaf9b84a3c9a8a473501caef845f55ea16c693e32f0b13c1cf02ada7ef7",
            "storageAddress": "http://testserver/model/53fbedaf9b84a3c9a8a473501caef845f55ea16c693e32f0b13c1cf02ada7ef7/file/"
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
        "key": "d376a672c7231fba31e23c868202e088a06783da48577654360025050eaf88cc",
        "algo": {
            "name": "Logistic regression",
            "hash": "9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d",
            "storageAddress": "http://testserver/algo/9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d/file/"
        },
        "creator": "MyOrg2MSP",
        "dataset": {
            "worker": "MyOrg2MSP",
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "e3644123451975be20909fcfd9c664a0573d9bfe04c5021625412d78c3536f1c"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 1
        },
        "computePlanID": "d376a672c7231fba31e23c868202e088a06783da48577654360025050eaf88cc",
        "inModels": None,
        "log": "",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "e5762042461c355761dd8986b510ea23494d5638a671370dabbf0ac73f8a3208",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outModel": {
            "hash": "97ba127dac7394c6af47b922c7d31aef9019fa26db803476170d44a389486f92",
            "storageAddress": "http://testserver/model/97ba127dac7394c6af47b922c7d31aef9019fa26db803476170d44a389486f92/file/"
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
        "key": "b835634d3ffb38fa98101619717aa07b62051ab2caa7be784dd1cfaef374d99a",
        "algo": {
            "name": "Logistic regression",
            "hash": "9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d",
            "storageAddress": "http://testserver/algo/9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d/file/"
        },
        "certified": True,
        "creator": "MyOrg2MSP",
        "dataset": {
            "worker": "MyOrg1MSP",
            "keys": [
                "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a",
                "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf"
            ],
            "openerHash": "ce9f292c72e9b82697445117f9c2d1d18ce0f8ed07ff91dadb17d668bddf8932",
            "perf": 0
        },
        "log": "",
        "traintupleKey": "d7e429016148abfac682ec6a183b7883ccb96cd375bb3c7f5d3c35816c04f7d6",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "e5762042461c355761dd8986b510ea23494d5638a671370dabbf0ac73f8a3208",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "status": "done",
        "tag": "substra"
    }
]

computeplan = [
    {
        "computePlanID": "d376a672c7231fba31e23c868202e088a06783da48577654360025050eaf88cc",
        "algoKey": "9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d",
        "objectiveKey": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
        "traintuples": [
            "d376a672c7231fba31e23c868202e088a06783da48577654360025050eaf88cc"
        ],
        "testtuples": None
    }
]

model = [
    {
        "traintuple": {
            "key": "c1d77d8e53f048b60863a1c453c60392e3f2b7b38dd0853f9b9664a5cef1c7cc",
            "algo": {
                "name": "Neural Network",
                "hash": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f",
                "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/file/"
            },
            "creator": "MyOrg2MSP",
            "dataset": {
                "worker": "MyOrg2MSP",
                "keys": [
                    "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
                "perf": 0
            },
            "computePlanID": "",
            "inModels": None,
            "log": "[01-01-0014-f7f130b]",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "e5762042461c355761dd8986b510ea23494d5638a671370dabbf0ac73f8a3208",
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
            "objective": None,
            "status": "",
            "tag": ""
        }
    },
    {
        "traintuple": {
            "key": "d7e429016148abfac682ec6a183b7883ccb96cd375bb3c7f5d3c35816c04f7d6",
            "algo": {
                "name": "Logistic regression",
                "hash": "9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d",
                "storageAddress": "http://testserver/algo/9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d/file/"
            },
            "creator": "MyOrg2MSP",
            "dataset": {
                "worker": "MyOrg2MSP",
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
                    "hash": "e5762042461c355761dd8986b510ea23494d5638a671370dabbf0ac73f8a3208",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "outModel": {
                "hash": "53fbedaf9b84a3c9a8a473501caef845f55ea16c693e32f0b13c1cf02ada7ef7",
                "storageAddress": "http://testserver/model/53fbedaf9b84a3c9a8a473501caef845f55ea16c693e32f0b13c1cf02ada7ef7/file/"
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
            "key": "b835634d3ffb38fa98101619717aa07b62051ab2caa7be784dd1cfaef374d99a",
            "algo": {
                "name": "Logistic regression",
                "hash": "9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d",
                "storageAddress": "http://testserver/algo/9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d/file/"
            },
            "certified": True,
            "creator": "MyOrg2MSP",
            "dataset": {
                "worker": "MyOrg1MSP",
                "keys": [
                    "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a",
                    "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf"
                ],
                "openerHash": "ce9f292c72e9b82697445117f9c2d1d18ce0f8ed07ff91dadb17d668bddf8932",
                "perf": 0
            },
            "log": "",
            "traintupleKey": "d7e429016148abfac682ec6a183b7883ccb96cd375bb3c7f5d3c35816c04f7d6",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "e5762042461c355761dd8986b510ea23494d5638a671370dabbf0ac73f8a3208",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "status": "done",
            "tag": "substra"
        }
    },
    {
        "traintuple": {
            "key": "a55fb929e12bca0be8e7d6db58bc7f5b6d2134c7c36d29961729da54d383dc01",
            "algo": {
                "name": "Random Forest",
                "hash": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9",
                "storageAddress": "http://testserver/algo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9/file/"
            },
            "creator": "MyOrg2MSP",
            "dataset": {
                "worker": "MyOrg2MSP",
                "keys": [
                    "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
                "perf": 0
            },
            "computePlanID": "",
            "inModels": None,
            "log": "[01-01-0014-01b28b3]",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "e5762042461c355761dd8986b510ea23494d5638a671370dabbf0ac73f8a3208",
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
            "objective": None,
            "status": "",
            "tag": ""
        }
    },
    {
        "traintuple": {
            "key": "d376a672c7231fba31e23c868202e088a06783da48577654360025050eaf88cc",
            "algo": {
                "name": "Logistic regression",
                "hash": "9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d",
                "storageAddress": "http://testserver/algo/9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d/file/"
            },
            "creator": "MyOrg2MSP",
            "dataset": {
                "worker": "MyOrg2MSP",
                "keys": [
                    "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                    "e3644123451975be20909fcfd9c664a0573d9bfe04c5021625412d78c3536f1c"
                ],
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
                "perf": 1
            },
            "computePlanID": "d376a672c7231fba31e23c868202e088a06783da48577654360025050eaf88cc",
            "inModels": None,
            "log": "",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "e5762042461c355761dd8986b510ea23494d5638a671370dabbf0ac73f8a3208",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "outModel": {
                "hash": "97ba127dac7394c6af47b922c7d31aef9019fa26db803476170d44a389486f92",
                "storageAddress": "http://testserver/model/97ba127dac7394c6af47b922c7d31aef9019fa26db803476170d44a389486f92/file/"
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
            "objective": None,
            "status": "",
            "tag": ""
        }
    }
]
