def metric_post_delete(sender, instance, **kwargs):
    # delete folder from MinioStorage
    instance.address.storage.delete(str(instance.address.name))
    instance.description.storage.delete(str(instance.description.name))
