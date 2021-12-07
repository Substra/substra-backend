def datamanager_post_delete(sender, instance, **kwargs):
    # delete folder and files from MinioStorage
    instance.data_opener.storage.delete(str(instance.data_opener.name))
    instance.description.storage.delete(str(instance.description.name))
