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
        "owner": "fba9c2538319fe2b45ac7047e21b4bc7196537367814d5da7f0aae020d3be5f7",
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
        "owner": "fba9c2538319fe2b45ac7047e21b4bc7196537367814d5da7f0aae020d3be5f7",
        "testDataset": {
            "dataManagerKey": "82e841c49822b2abcab9e95fe9ae359316d70ab5f627a28b0b67618dd945b2c2",
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
            "storageAddress": "http://testserver/data_manager/615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7/description/"
        },
        "key": "615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7",
        "name": "ISIC 2018",
        "opener": {
            "hash": "615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7",
            "storageAddress": "http://testserver/data_manager/615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7/opener/"
        },
        "owner": "2cb13d299b337fae2969da1ff4ddd9a2f3004be52d64f671d13d9513f5a79426",
        "permissions": "all",
        "type": "Images"
    },
    {
        "objectiveKey": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
        "description": {
            "hash": "258bef187a166b3fef5cb86e68c8f7e154c283a148cd5bc344fec7e698821ad3",
            "storageAddress": "http://testserver/data_manager/82e841c49822b2abcab9e95fe9ae359316d70ab5f627a28b0b67618dd945b2c2/description/"
        },
        "key": "82e841c49822b2abcab9e95fe9ae359316d70ab5f627a28b0b67618dd945b2c2",
        "name": "Simplified ISIC 2018",
        "opener": {
            "hash": "82e841c49822b2abcab9e95fe9ae359316d70ab5f627a28b0b67618dd945b2c2",
            "storageAddress": "http://testserver/data_manager/82e841c49822b2abcab9e95fe9ae359316d70ab5f627a28b0b67618dd945b2c2/opener/"
        },
        "owner": "fba9c2538319fe2b45ac7047e21b4bc7196537367814d5da7f0aae020d3be5f7",
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
        "owner": "2cb13d299b337fae2969da1ff4ddd9a2f3004be52d64f671d13d9513f5a79426",
        "permissions": "all"
    },
    {
        "key": "4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7",
        "name": "Logistic regression",
        "content": {
            "hash": "4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7",
            "storageAddress": "http://testserver/algo/4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7/file/"
        },
        "description": {
            "hash": "124a0425b746d7072282d167b53cb6aab3a31bf1946dae89135c15b0126ebec3",
            "storageAddress": "http://testserver/algo/4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7/description/"
        },
        "owner": "2cb13d299b337fae2969da1ff4ddd9a2f3004be52d64f671d13d9513f5a79426",
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
        "owner": "2cb13d299b337fae2969da1ff4ddd9a2f3004be52d64f671d13d9513f5a79426",
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
        "creator": "2cb13d299b337fae2969da1ff4ddd9a2f3004be52d64f671d13d9513f5a79426",
        "dataset": {
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7",
            "perf": 0,
            "worker": "2cb13d299b337fae2969da1ff4ddd9a2f3004be52d64f671d13d9513f5a79426"
        },
        "fltask": "",
        "inModels": None,
        "key": "c4e3116dd3f895986b77e4d445178330630bd3f52407f10462dd4778e40090e0",
        "log": "[00-01-0032-7cc5b61]",
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
        "algo": {
            "hash": "4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7",
            "name": "Logistic regression",
            "storageAddress": "http://testserver/algo/4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7/file/"
        },
        "creator": "2cb13d299b337fae2969da1ff4ddd9a2f3004be52d64f671d13d9513f5a79426",
        "dataset": {
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7",
            "perf": 1,
            "worker": "2cb13d299b337fae2969da1ff4ddd9a2f3004be52d64f671d13d9513f5a79426"
        },
        "fltask": "",
        "inModels": None,
        "key": "3979576752e014adddadfc360d79c67cdccb0f4bae46936f35ce09c64e5832c8",
        "log": "Train - CPU:173.81 % - Mem:0.11 GB - GPU:0.00 % - GPU Mem:0.00 GB; ",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "c42dca31fbc2ebb5705643e3bb6ee666bbfd956de13dd03727f825ad8445b4d7",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outModel": {
            "hash": "592242f9b162178994897c5b8aa49450a17cc395bb9bc9864b830a6cdba6a075",
            "storageAddress": "http://testserver/model/592242f9b162178994897c5b8aa49450a17cc395bb9bc9864b830a6cdba6a075/file/"
        },
        "permissions": "all",
        "rank": 0,
        "status": "done",
        "tag": "substra"
    },
    {
        "algo": {
            "hash": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9",
            "name": "Random Forest",
            "storageAddress": "http://testserver/algo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9/file/"
        },
        "creator": "2cb13d299b337fae2969da1ff4ddd9a2f3004be52d64f671d13d9513f5a79426",
        "dataset": {
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7",
            "perf": 0,
            "worker": "2cb13d299b337fae2969da1ff4ddd9a2f3004be52d64f671d13d9513f5a79426"
        },
        "fltask": "",
        "inModels": None,
        "key": "c6beed3a4ee5ead0c4246faac7931a944fc2286e193454bb1b851dee0c5a5f59",
        "log": "[00-01-0032-139c39e]",
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
        "key": "b7b9291e5ff96ec7d16d38ab49915cbe15055347bb933a824887f2a76fb57c9a",
        "algo": {
            "name": "Logistic regression",
            "hash": "4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7",
            "storageAddress": "http://testserver/algo/4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7/file/"
        },
        "certified": True,
        "creator": "2cb13d299b337fae2969da1ff4ddd9a2f3004be52d64f671d13d9513f5a79426",
        "dataset": {
            "worker": "fba9c2538319fe2b45ac7047e21b4bc7196537367814d5da7f0aae020d3be5f7",
            "keys": [
                "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a",
                "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf"
            ],
            "openerHash": "82e841c49822b2abcab9e95fe9ae359316d70ab5f627a28b0b67618dd945b2c2",
            "perf": 0
        },
        "log": "Test - CPU:179.46 % - Mem:0.09 GB - GPU:0.00 % - GPU Mem:0.00 GB; ",
        "model": {
            "traintupleKey": "3979576752e014adddadfc360d79c67cdccb0f4bae46936f35ce09c64e5832c8",
            "hash": "592242f9b162178994897c5b8aa49450a17cc395bb9bc9864b830a6cdba6a075",
            "storageAddress": "http://testserver/model/592242f9b162178994897c5b8aa49450a17cc395bb9bc9864b830a6cdba6a075/file/"
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
        "testtuple": {
            "algo": {
                "hash": "4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7",
                "name": "Logistic regression",
                "storageAddress": "http://testserver/algo/4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7/file/"
            },
            "certified": True,
            "creator": "2cb13d299b337fae2969da1ff4ddd9a2f3004be52d64f671d13d9513f5a79426",
            "dataset": {
                "keys": [
                    "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a",
                    "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf"
                ],
                "openerHash": "82e841c49822b2abcab9e95fe9ae359316d70ab5f627a28b0b67618dd945b2c2",
                "perf": 0,
                "worker": "fba9c2538319fe2b45ac7047e21b4bc7196537367814d5da7f0aae020d3be5f7"
            },
            "key": "b7b9291e5ff96ec7d16d38ab49915cbe15055347bb933a824887f2a76fb57c9a",
            "log": "Test - CPU:179.46 % - Mem:0.09 GB - GPU:0.00 % - GPU Mem:0.00 GB; ",
            "model": {
                "hash": "592242f9b162178994897c5b8aa49450a17cc395bb9bc9864b830a6cdba6a075",
                "storageAddress": "http://testserver/model/592242f9b162178994897c5b8aa49450a17cc395bb9bc9864b830a6cdba6a075/file/",
                "traintupleKey": "3979576752e014adddadfc360d79c67cdccb0f4bae46936f35ce09c64e5832c8"
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
        },
        "traintuple": {
            "algo": {
                "hash": "4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7",
                "name": "Logistic regression",
                "storageAddress": "http://testserver/algo/4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7/file/"
            },
            "creator": "2cb13d299b337fae2969da1ff4ddd9a2f3004be52d64f671d13d9513f5a79426",
            "dataset": {
                "keys": [
                    "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7",
                "perf": 1,
                "worker": "2cb13d299b337fae2969da1ff4ddd9a2f3004be52d64f671d13d9513f5a79426"
            },
            "fltask": "",
            "inModels": None,
            "key": "3979576752e014adddadfc360d79c67cdccb0f4bae46936f35ce09c64e5832c8",
            "log": "Train - CPU:173.81 % - Mem:0.11 GB - GPU:0.00 % - GPU Mem:0.00 GB; ",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "c42dca31fbc2ebb5705643e3bb6ee666bbfd956de13dd03727f825ad8445b4d7",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "outModel": {
                "hash": "592242f9b162178994897c5b8aa49450a17cc395bb9bc9864b830a6cdba6a075",
                "storageAddress": "http://testserver/model/592242f9b162178994897c5b8aa49450a17cc395bb9bc9864b830a6cdba6a075/file/"
            },
            "permissions": "all",
            "rank": 0,
            "status": "done",
            "tag": "substra"
        }
    }
]

