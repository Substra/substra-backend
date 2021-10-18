from substrapp.storages.minio import MinioStorage


def model_post_delete(sender, instance, **kwargs):
    # delete file from MinioStorage
    if isinstance(instance.file.storage, MinioStorage):
        instance.file.storage.delete(str(instance.file.name))
