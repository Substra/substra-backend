def organization_pre_save(sender, instance, **kwargs):
    instance.set_password(instance.secret)
