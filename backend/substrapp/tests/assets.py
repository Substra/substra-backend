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
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca"
        },
        "computePlanID": "",
        "inModels": None,
        "log": "[00-01-0032-d50bc08]",
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
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca"
        },
        "computePlanID": "",
        "inModels": None,
        "log": "[00-01-0032-5bd86f9]",
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
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca"
        },
        "computePlanID": "2341f3e69a54010176575567aa7c2e728405c89969a6354dbf21cf477e986c42",
        "inModels": None,
        "log": "",
        "outModel": {
            "hash": "14ea126a4c0cef4378aabce7157794c5d2d7f9dcf7057826805b2a12f90fd0f0",
            "storageAddress": "http://testserver/model/14ea126a4c0cef4378aabce7157794c5d2d7f9dcf7057826805b2a12f90fd0f0/file/"
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
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca"
        },
        "computePlanID": "",
        "inModels": None,
        "log": "",
        "outModel": {
            "hash": "149f94d883cff77f5770b10f9ca54b817a9362d8f36f370d7138939679a0f78e",
            "storageAddress": "http://testserver/model/149f94d883cff77f5770b10f9ca54b817a9362d8f36f370d7138939679a0f78e/file/"
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
        "algo": {
            "name": "Logistic regression",
            "hash": "9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d",
            "storageAddress": "http://testserver/algo/9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d/file/"
        },
        "certified": True,
        "computePlanID": "",
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
        "key": "b835634d3ffb38fa98101619717aa07b62051ab2caa7be784dd1cfaef374d99a",
        "log": "",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "e5762042461c355761dd8986b510ea23494d5638a671370dabbf0ac73f8a3208",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "rank": 0,
        "status": "done",
        "tag": "substra",
        "traintupleKey": "d7e429016148abfac682ec6a183b7883ccb96cd375bb3c7f5d3c35816c04f7d6",
        "traintupleType": "traintuple"
    }
]

computeplan = [
    {
        "computePlanID": "2341f3e69a54010176575567aa7c2e728405c89969a6354dbf21cf477e986c42",
        "traintupleKeys": [
            "d376a672c7231fba31e23c868202e088a06783da48577654360025050eaf88cc"
        ],
        "aggregatetupleKeys": None,
        "compositeTraintupleKeys": None,
        "testtupleKeys": None,
        "tag": "",
        "status": "done",
        "tupleCount": 1,
        "doneCount": 1
    }
]

compositetraintuple = [
    {
        "key": "e83d39acb3870a06f46d92bcc251cc54e6f96d5be756a08fcba321819b86333f",
        "algo": {
            "name": "Logistic regression (composite)",
            "hash": "468a18f9c9dedefa32d266c8263f117cd0e859ffecf531d2b90a220559acd96f",
            "storageAddress": "http://testserver/composite_algo/468a18f9c9dedefa32d266c8263f117cd0e859ffecf531d2b90a220559acd96f/file/"
        },
        "creator": "MyOrg1MSP",
        "dataset": {
            "worker": "MyOrg2MSP",
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca"
        },
        "computePlanID": "",
        "inHeadModel": None,
        "inTrunkModel": None,
        "log": "",
        "outHeadModel": {
            "outModel": {
                "hash": "df3f74523a807d0c2b06abffb0a1ca4d44c6a121dc61280608caab5fba450ee9",
                "storageAddress": "http://testserver/model/df3f74523a807d0c2b06abffb0a1ca4d44c6a121dc61280608caab5fba450ee9/file/"
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
                "hash": "2485b8f0bed25260684d8052ab6f77e0817e821eaea8acd763ed8e64701d9b47",
                "storageAddress": "http://testserver/model/2485b8f0bed25260684d8052ab6f77e0817e821eaea8acd763ed8e64701d9b47/file/"
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
        "tag": "substra"
    }
]

compositealgo = [
    {
        "key": "468a18f9c9dedefa32d266c8263f117cd0e859ffecf531d2b90a220559acd96f",
        "name": "Logistic regression (composite)",
        "content": {
            "hash": "468a18f9c9dedefa32d266c8263f117cd0e859ffecf531d2b90a220559acd96f",
            "storageAddress": "http://testserver/composite_algo/468a18f9c9dedefa32d266c8263f117cd0e859ffecf531d2b90a220559acd96f/file/"
        },
        "description": {
            "hash": "a5108cfd377dce09c5c2e439fc1527e4b50128099b1e8ec525b6e4dc85f7300f",
            "storageAddress": "http://testserver/composite_algo/468a18f9c9dedefa32d266c8263f117cd0e859ffecf531d2b90a220559acd96f/description/"
        },
        "owner": "MyOrg1MSP",
        "permissions": {
            "process": {
                "public": True,
                "authorizedIDs": []
            }
        }
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
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca"
            },
            "computePlanID": "",
            "inModels": None,
            "log": "[00-01-0032-d50bc08]",
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
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
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
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca"
            },
            "computePlanID": "",
            "inModels": None,
            "log": "[00-01-0032-5bd86f9]",
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
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
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
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca"
            },
            "computePlanID": "2341f3e69a54010176575567aa7c2e728405c89969a6354dbf21cf477e986c42",
            "inModels": None,
            "log": "",
            "outModel": {
                "hash": "14ea126a4c0cef4378aabce7157794c5d2d7f9dcf7057826805b2a12f90fd0f0",
                "storageAddress": "http://testserver/model/14ea126a4c0cef4378aabce7157794c5d2d7f9dcf7057826805b2a12f90fd0f0/file/"
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
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
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
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca"
            },
            "computePlanID": "",
            "inModels": None,
            "log": "",
            "outModel": {
                "hash": "149f94d883cff77f5770b10f9ca54b817a9362d8f36f370d7138939679a0f78e",
                "storageAddress": "http://testserver/model/149f94d883cff77f5770b10f9ca54b817a9362d8f36f370d7138939679a0f78e/file/"
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
                "name": "Logistic regression",
                "hash": "9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d",
                "storageAddress": "http://testserver/algo/9fe61782e7b4d445dff6bc0baae01eb3fa6e926ad0f6870365d605eee5bd169d/file/"
            },
            "certified": True,
            "computePlanID": "",
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
            "key": "b835634d3ffb38fa98101619717aa07b62051ab2caa7be784dd1cfaef374d99a",
            "log": "",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "e5762042461c355761dd8986b510ea23494d5638a671370dabbf0ac73f8a3208",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "rank": 0,
            "status": "done",
            "tag": "substra",
            "traintupleKey": "d7e429016148abfac682ec6a183b7883ccb96cd375bb3c7f5d3c35816c04f7d6",
            "traintupleType": "traintuple"
        }
    },
    {
        "compositeTraintuple": {
            "key": "e83d39acb3870a06f46d92bcc251cc54e6f96d5be756a08fcba321819b86333f",
            "algo": {
                "name": "Logistic regression (composite)",
                "hash": "468a18f9c9dedefa32d266c8263f117cd0e859ffecf531d2b90a220559acd96f",
                "storageAddress": "http://testserver/composite_algo/468a18f9c9dedefa32d266c8263f117cd0e859ffecf531d2b90a220559acd96f/file/"
            },
            "creator": "MyOrg1MSP",
            "dataset": {
                "worker": "MyOrg2MSP",
                "keys": [
                    "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca"
            },
            "computePlanID": "",
            "inHeadModel": None,
            "inTrunkModel": None,
            "log": "",
            "outHeadModel": {
                "outModel": {
                    "hash": "df3f74523a807d0c2b06abffb0a1ca4d44c6a121dc61280608caab5fba450ee9",
                    "storageAddress": "http://testserver/model/df3f74523a807d0c2b06abffb0a1ca4d44c6a121dc61280608caab5fba450ee9/file/"
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
                    "hash": "2485b8f0bed25260684d8052ab6f77e0817e821eaea8acd763ed8e64701d9b47",
                    "storageAddress": "http://testserver/model/2485b8f0bed25260684d8052ab6f77e0817e821eaea8acd763ed8e64701d9b47/file/"
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
            "tag": "substra"
        },
        "testtuple": {
            "algo": None,
            "certified": False,
            "computePlanID": "",
            "creator": "",
            "dataset": None,
            "key": "",
            "log": "",
            "objective": None,
            "rank": 0,
            "status": "",
            "tag": "",
            "traintupleKey": "",
            "traintupleType": ""
        }
    }
]

