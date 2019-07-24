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
        "owner": "cc89c43e621de4e2251505ce71f48111cfc2cdc46307eb2d01616d0ccfae3eac",
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
        "owner": "cc89c43e621de4e2251505ce71f48111cfc2cdc46307eb2d01616d0ccfae3eac",
        "testDataset": {
            "dataManagerKey": "82e841c49822b2abcab9e95fe9ae359316d70ab5f627a28b0b67618dd945b2c2",
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
            "storageAddress": "http://testserver/data_manager/615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7/description/"
        },
        "key": "615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7",
        "name": "ISIC 2018",
        "opener": {
            "hash": "615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7",
            "storageAddress": "http://testserver/data_manager/615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7/opener/"
        },
        "owner": "2849eac88763d23f65706b81cc63056712a170e5915e210640846c3ab4abea55",
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
        "owner": "cc89c43e621de4e2251505ce71f48111cfc2cdc46307eb2d01616d0ccfae3eac",
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
        "owner": "2849eac88763d23f65706b81cc63056712a170e5915e210640846c3ab4abea55",
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
        "owner": "2849eac88763d23f65706b81cc63056712a170e5915e210640846c3ab4abea55",
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
        "owner": "cc89c43e621de4e2251505ce71f48111cfc2cdc46307eb2d01616d0ccfae3eac",
        "permissions": "all"
    }
]

traintuple = [
    {
        "key": "e0db5d9206a9049dd57736943e6c79b7b0b5d369971725284bada0ad10b6d2e4",
        "algo": {
            "name": "Neural Network",
            "hash": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f",
            "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/file/"
        },
        "creator": "2849eac88763d23f65706b81cc63056712a170e5915e210640846c3ab4abea55",
        "dataset": {
            "worker": "2849eac88763d23f65706b81cc63056712a170e5915e210640846c3ab4abea55",
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7",
            "perf": 0
        },
        "fltask": "",
        "inModels": None,
        "log": "[00-01-0032-5246056]",
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
        "key": "e60b3a73927eda5ccd94620693e3dd056dee289bce0a3a0865b03b3359ab0ce4",
        "algo": {
            "name": "Logistic regression",
            "hash": "4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7",
            "storageAddress": "http://testserver/algo/4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7/file/"
        },
        "creator": "2849eac88763d23f65706b81cc63056712a170e5915e210640846c3ab4abea55",
        "dataset": {
            "worker": "2849eac88763d23f65706b81cc63056712a170e5915e210640846c3ab4abea55",
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7",
            "perf": 1
        },
        "fltask": "",
        "inModels": None,
        "log": "Train - CPU:89.48 % - Mem:0.11 GB - GPU:0.00 % - GPU Mem:0.00 GB;",
        "objective": {
            "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
            "metrics": {
                "hash": "c42dca31fbc2ebb5705643e3bb6ee666bbfd956de13dd03727f825ad8445b4d7",
                "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
            }
        },
        "outModel": {
            "hash": "72a0af902268420e04fcd06d50f97ed3015fc106f1b24af533451b55a00e7080",
            "storageAddress": "http://testserver/model/72a0af902268420e04fcd06d50f97ed3015fc106f1b24af533451b55a00e7080/file/"
        },
        "permissions": "all",
        "rank": 0,
        "status": "done",
        "tag": "substra"
    },
    {
        "key": "689990aac749b241b080fb6ee2c73aa30f442cb9056bd9803e75a7606dcdfb91",
        "algo": {
            "name": "Random Forest",
            "hash": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9",
            "storageAddress": "http://testserver/algo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9/file/"
        },
        "creator": "2849eac88763d23f65706b81cc63056712a170e5915e210640846c3ab4abea55",
        "dataset": {
            "worker": "2849eac88763d23f65706b81cc63056712a170e5915e210640846c3ab4abea55",
            "keys": [
                "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
            ],
            "openerHash": "615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7",
            "perf": 0
        },
        "fltask": "",
        "inModels": None,
        "log": "[00-01-0032-c370fb8]",
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
        "key": "915fdcc3406b6bf149a9d178f6e61d6c87a057a9ed8c10b369422b74ce4d3394",
        "algo": {
            "name": "Logistic regression",
            "hash": "4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7",
            "storageAddress": "http://testserver/algo/4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7/file/"
        },
        "certified": True,
        "creator": "2849eac88763d23f65706b81cc63056712a170e5915e210640846c3ab4abea55",
        "dataset": {
            "worker": "cc89c43e621de4e2251505ce71f48111cfc2cdc46307eb2d01616d0ccfae3eac",
            "keys": [
                "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a",
                "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf"
            ],
            "openerHash": "82e841c49822b2abcab9e95fe9ae359316d70ab5f627a28b0b67618dd945b2c2",
            "perf": 0
        },
        "log": "Test - CPU:0.00 % - Mem:0.00 GB - GPU:0.00 % - GPU Mem:0.00 GB;",
        "model": {
            "traintupleKey": "e60b3a73927eda5ccd94620693e3dd056dee289bce0a3a0865b03b3359ab0ce4",
            "hash": "72a0af902268420e04fcd06d50f97ed3015fc106f1b24af533451b55a00e7080",
            "storageAddress": "http://testserver/model/72a0af902268420e04fcd06d50f97ed3015fc106f1b24af533451b55a00e7080/file/"
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
            "key": "e0db5d9206a9049dd57736943e6c79b7b0b5d369971725284bada0ad10b6d2e4",
            "algo": {
                "name": "Neural Network",
                "hash": "0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f",
                "storageAddress": "http://testserver/algo/0acc5180e09b6a6ac250f4e3c172e2893f617aa1c22ef1f379019d20fe44142f/file/"
            },
            "creator": "2849eac88763d23f65706b81cc63056712a170e5915e210640846c3ab4abea55",
            "dataset": {
                "worker": "2849eac88763d23f65706b81cc63056712a170e5915e210640846c3ab4abea55",
                "keys": [
                    "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7",
                "perf": 0
            },
            "fltask": "",
            "inModels": None,
            "log": "[00-01-0032-5246056]",
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
            "key": "e60b3a73927eda5ccd94620693e3dd056dee289bce0a3a0865b03b3359ab0ce4",
            "algo": {
                "name": "Logistic regression",
                "hash": "4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7",
                "storageAddress": "http://testserver/algo/4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7/file/"
            },
            "creator": "2849eac88763d23f65706b81cc63056712a170e5915e210640846c3ab4abea55",
            "dataset": {
                "worker": "2849eac88763d23f65706b81cc63056712a170e5915e210640846c3ab4abea55",
                "keys": [
                    "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7",
                "perf": 1
            },
            "fltask": "",
            "inModels": None,
            "log": "Train - CPU:89.48 % - Mem:0.11 GB - GPU:0.00 % - GPU Mem:0.00 GB;",
            "objective": {
                "hash": "3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71",
                "metrics": {
                    "hash": "c42dca31fbc2ebb5705643e3bb6ee666bbfd956de13dd03727f825ad8445b4d7",
                    "storageAddress": "http://testserver/objective/3d70ab46d710dacb0f48cb42db4874fac14e048a0d415e266aad38c09591ee71/metrics/"
                }
            },
            "outModel": {
                "hash": "72a0af902268420e04fcd06d50f97ed3015fc106f1b24af533451b55a00e7080",
                "storageAddress": "http://testserver/model/72a0af902268420e04fcd06d50f97ed3015fc106f1b24af533451b55a00e7080/file/"
            },
            "permissions": "all",
            "rank": 0,
            "status": "done",
            "tag": "substra"
        },
        "testtuple": {
            "key": "915fdcc3406b6bf149a9d178f6e61d6c87a057a9ed8c10b369422b74ce4d3394",
            "algo": {
                "name": "Logistic regression",
                "hash": "4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7",
                "storageAddress": "http://testserver/algo/4cc53726e01f7e3864a6cf9da24d9cef04a7cbd7fd2892765ff76931dd4628e7/file/"
            },
            "certified": True,
            "creator": "2849eac88763d23f65706b81cc63056712a170e5915e210640846c3ab4abea55",
            "dataset": {
                "worker": "cc89c43e621de4e2251505ce71f48111cfc2cdc46307eb2d01616d0ccfae3eac",
                "keys": [
                    "17d58b67ae2028018108c9bf555fa58b2ddcfe560e0117294196e79d26140b2a",
                    "8bf3bf4f753a32f27d18c86405e7a406a83a55610d91abcca9acc525061b8ecf"
                ],
                "openerHash": "82e841c49822b2abcab9e95fe9ae359316d70ab5f627a28b0b67618dd945b2c2",
                "perf": 0
            },
            "log": "Test - CPU:0.00 % - Mem:0.00 GB - GPU:0.00 % - GPU Mem:0.00 GB;",
            "model": {
                "traintupleKey": "e60b3a73927eda5ccd94620693e3dd056dee289bce0a3a0865b03b3359ab0ce4",
                "hash": "72a0af902268420e04fcd06d50f97ed3015fc106f1b24af533451b55a00e7080",
                "storageAddress": "http://testserver/model/72a0af902268420e04fcd06d50f97ed3015fc106f1b24af533451b55a00e7080/file/"
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
            "key": "689990aac749b241b080fb6ee2c73aa30f442cb9056bd9803e75a7606dcdfb91",
            "algo": {
                "name": "Random Forest",
                "hash": "9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9",
                "storageAddress": "http://testserver/algo/9c3d8777e11fd72cbc0fd672bec3a0848f8518b4d56706008cc05f8a1cee44f9/file/"
            },
            "creator": "2849eac88763d23f65706b81cc63056712a170e5915e210640846c3ab4abea55",
            "dataset": {
                "worker": "2849eac88763d23f65706b81cc63056712a170e5915e210640846c3ab4abea55",
                "keys": [
                    "31510dc1d8be788f7c5d28d05714f7efb9edb667762966b9adc02eadeaacebe9",
                    "03a1f878768ea8624942d46a3b438c37992e626c2cf655023bcc3bed69d485d1"
                ],
                "openerHash": "615ce631b93c185b492dfc97ed5dea27430d871fa4e50678bab3c79ce2ec6cb7",
                "perf": 0
            },
            "fltask": "",
            "inModels": None,
            "log": "[00-01-0032-c370fb8]",
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

