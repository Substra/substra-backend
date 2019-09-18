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
            "hash": "506dacd8800c36e70ad3df7379c9164e03452d700bd2c3edb472e6bd0dc01f2e",
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
            "hash": "506dacd8800c36e70ad3df7379c9164e03452d700bd2c3edb472e6bd0dc01f2e",
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
        "key": "6523012b72bcd0299f709bc6aaa084d2092dddb9a6256fbffa64645478995a1d",
        "name": "Logistic regression",
        "content": {
            "hash": "6523012b72bcd0299f709bc6aaa084d2092dddb9a6256fbffa64645478995a1d",
            "storageAddress": "http://testserver/algo/6523012b72bcd0299f709bc6aaa084d2092dddb9a6256fbffa64645478995a1d/file/"
        },
        "description": {
            "hash": "124a0425b746d7072282d167b53cb6aab3a31bf1946dae89135c15b0126ebec3",
            "storageAddress": "http://testserver/algo/6523012b72bcd0299f709bc6aaa084d2092dddb9a6256fbffa64645478995a1d/description/"
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
        "key": "363f70dcc3bf22fdce65e36c957e855b7cd3e2828e6909f34ccc97ee6218541a",
        "algo": {
            "name": "Neural Network",
            "hash": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f",
            "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/file/"
        },
        "creator": "chu-nantesMSP",
        "dataset": {
            "worker": "chu-nantesMSP",
            "keys": [
                "dacc0288138cb50569250f996bbe716ec8968fb334d32f29f174c9e79a224127",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 0
        },
        "computePlanID": "",
        "inModels": None,
        "log": "[00-01-0032-e18ebeb]",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "506dacd8800c36e70ad3df7379c9164e03452d700bd2c3edb472e6bd0dc01f2e",
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
        "key": "05b44fa4b94d548e35922629f7b23dd84f777d09925bbecb0362081ca528f746",
        "algo": {
            "name": "Logistic regression",
            "hash": "6523012b72bcd0299f709bc6aaa084d2092dddb9a6256fbffa64645478995a1d",
            "storageAddress": "http://testserver/algo/6523012b72bcd0299f709bc6aaa084d2092dddb9a6256fbffa64645478995a1d/file/"
        },
        "creator": "chu-nantesMSP",
        "dataset": {
            "worker": "chu-nantesMSP",
            "keys": [
                "dacc0288138cb50569250f996bbe716ec8968fb334d32f29f174c9e79a224127",
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
                "hash": "506dacd8800c36e70ad3df7379c9164e03452d700bd2c3edb472e6bd0dc01f2e",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outModel": {
            "hash": "e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff99",
            "storageAddress": "http://testserver/model/e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff99/file/"
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
        "key": "32070e156eb4f97d85ff8448ea2ab71f4f275ab845159029354e4446aff974e0",
        "algo": {
            "name": "Logistic regression",
            "hash": "6523012b72bcd0299f709bc6aaa084d2092dddb9a6256fbffa64645478995a1d",
            "storageAddress": "http://testserver/algo/6523012b72bcd0299f709bc6aaa084d2092dddb9a6256fbffa64645478995a1d/file/"
        },
        "creator": "chu-nantesMSP",
        "dataset": {
            "worker": "chu-nantesMSP",
            "keys": [
                "dacc0288138cb50569250f996bbe716ec8968fb334d32f29f174c9e79a224127",
                "e3644123451975be20909fcfd9c664a0573d9bfe04c5021625412d78c3536f1c"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 1
        },
        "computePlanID": "32070e156eb4f97d85ff8448ea2ab71f4f275ab845159029354e4446aff974e0",
        "inModels": None,
        "log": "",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "506dacd8800c36e70ad3df7379c9164e03452d700bd2c3edb472e6bd0dc01f2e",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outModel": {
            "hash": "0b1ce6f2bd9247a262c3695aa07aad5ef187197f118c73c60a42e176f8f53b98",
            "storageAddress": "http://testserver/model/0b1ce6f2bd9247a262c3695aa07aad5ef187197f118c73c60a42e176f8f53b98/file/"
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
        "key": "a2171a1c09738c677748346d22d2b5eea47f874a3b4f4b75224674235892de72",
        "algo": {
            "name": "Random Forest",
            "hash": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9",
            "storageAddress": "http://testserver/algo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9/file/"
        },
        "creator": "chu-nantesMSP",
        "dataset": {
            "worker": "chu-nantesMSP",
            "keys": [
                "dacc0288138cb50569250f996bbe716ec8968fb334d32f29f174c9e79a224127",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
            "perf": 0
        },
        "computePlanID": "",
        "inModels": None,
        "log": "[00-01-0032-8189cc5]",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "506dacd8800c36e70ad3df7379c9164e03452d700bd2c3edb472e6bd0dc01f2e",
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
        "key": "b2d127e65583080bf85d51f4bbc6b04e420414dd668f921c419eb6f078e428ae",
        "algo": {
            "name": "Logistic regression",
            "hash": "6523012b72bcd0299f709bc6aaa084d2092dddb9a6256fbffa64645478995a1d",
            "storageAddress": "http://testserver/algo/6523012b72bcd0299f709bc6aaa084d2092dddb9a6256fbffa64645478995a1d/file/"
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
            "traintupleKey": "05b44fa4b94d548e35922629f7b23dd84f777d09925bbecb0362081ca528f746",
            "hash": "e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff99",
            "storageAddress": "http://testserver/model/e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff99/file/"
        },
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "506dacd8800c36e70ad3df7379c9164e03452d700bd2c3edb472e6bd0dc01f2e",
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
            "key": "363f70dcc3bf22fdce65e36c957e855b7cd3e2828e6909f34ccc97ee6218541a",
            "algo": {
                "name": "Neural Network",
                "hash": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f",
                "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/file/"
            },
            "creator": "chu-nantesMSP",
            "dataset": {
                "worker": "chu-nantesMSP",
                "keys": [
                    "dacc0288138cb50569250f996bbe716ec8968fb334d32f29f174c9e79a224127",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
                "perf": 0
            },
            "computePlanID": "",
            "inModels": None,
            "log": "[00-01-0032-e18ebeb]",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "506dacd8800c36e70ad3df7379c9164e03452d700bd2c3edb472e6bd0dc01f2e",
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
            "key": "05b44fa4b94d548e35922629f7b23dd84f777d09925bbecb0362081ca528f746",
            "algo": {
                "name": "Logistic regression",
                "hash": "6523012b72bcd0299f709bc6aaa084d2092dddb9a6256fbffa64645478995a1d",
                "storageAddress": "http://testserver/algo/6523012b72bcd0299f709bc6aaa084d2092dddb9a6256fbffa64645478995a1d/file/"
            },
            "creator": "chu-nantesMSP",
            "dataset": {
                "worker": "chu-nantesMSP",
                "keys": [
                    "dacc0288138cb50569250f996bbe716ec8968fb334d32f29f174c9e79a224127",
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
                    "hash": "506dacd8800c36e70ad3df7379c9164e03452d700bd2c3edb472e6bd0dc01f2e",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "outModel": {
                "hash": "e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff99",
                "storageAddress": "http://testserver/model/e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff99/file/"
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
            "key": "b2d127e65583080bf85d51f4bbc6b04e420414dd668f921c419eb6f078e428ae",
            "algo": {
                "name": "Logistic regression",
                "hash": "6523012b72bcd0299f709bc6aaa084d2092dddb9a6256fbffa64645478995a1d",
                "storageAddress": "http://testserver/algo/6523012b72bcd0299f709bc6aaa084d2092dddb9a6256fbffa64645478995a1d/file/"
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
                "traintupleKey": "05b44fa4b94d548e35922629f7b23dd84f777d09925bbecb0362081ca528f746",
                "hash": "e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff99",
                "storageAddress": "http://testserver/model/e6a16f5bea8a485f48a8aa8c462155d2d500022a9459c1ff4b3c32acd168ff99/file/"
            },
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "506dacd8800c36e70ad3df7379c9164e03452d700bd2c3edb472e6bd0dc01f2e",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "status": "done",
            "tag": "substra"
        }
    },
    {
        "traintuple": {
            "key": "32070e156eb4f97d85ff8448ea2ab71f4f275ab845159029354e4446aff974e0",
            "algo": {
                "name": "Logistic regression",
                "hash": "6523012b72bcd0299f709bc6aaa084d2092dddb9a6256fbffa64645478995a1d",
                "storageAddress": "http://testserver/algo/6523012b72bcd0299f709bc6aaa084d2092dddb9a6256fbffa64645478995a1d/file/"
            },
            "creator": "chu-nantesMSP",
            "dataset": {
                "worker": "chu-nantesMSP",
                "keys": [
                    "dacc0288138cb50569250f996bbe716ec8968fb334d32f29f174c9e79a224127",
                    "e3644123451975be20909fcfd9c664a0573d9bfe04c5021625412d78c3536f1c"
                ],
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
                "perf": 1
            },
            "computePlanID": "32070e156eb4f97d85ff8448ea2ab71f4f275ab845159029354e4446aff974e0",
            "inModels": None,
            "log": "",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "506dacd8800c36e70ad3df7379c9164e03452d700bd2c3edb472e6bd0dc01f2e",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "outModel": {
                "hash": "0b1ce6f2bd9247a262c3695aa07aad5ef187197f118c73c60a42e176f8f53b98",
                "storageAddress": "http://testserver/model/0b1ce6f2bd9247a262c3695aa07aad5ef187197f118c73c60a42e176f8f53b98/file/"
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
            "key": "a2171a1c09738c677748346d22d2b5eea47f874a3b4f4b75224674235892de72",
            "algo": {
                "name": "Random Forest",
                "hash": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9",
                "storageAddress": "http://testserver/algo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9/file/"
            },
            "creator": "chu-nantesMSP",
            "dataset": {
                "worker": "chu-nantesMSP",
                "keys": [
                    "dacc0288138cb50569250f996bbe716ec8968fb334d32f29f174c9e79a224127",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "8dd01465003a9b1e01c99c904d86aa518b3a5dd9dc8d40fe7d075c726ac073ca",
                "perf": 0
            },
            "computePlanID": "",
            "inModels": None,
            "log": "[00-01-0032-8189cc5]",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "506dacd8800c36e70ad3df7379c9164e03452d700bd2c3edb472e6bd0dc01f2e",
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
