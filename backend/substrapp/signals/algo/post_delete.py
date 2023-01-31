def function_post_delete(sender, instance, **kwargs):
    # delete folder from MinioStorage
    instance.file.storage.delete(str(instance.file.name))
    instance.description.storage.delete(str(instance.description.name))
