def node_pre_save(sender, instance, **kwargs):
    instance.set_password(instance.secret)
