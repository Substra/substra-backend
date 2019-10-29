from django.db import models

def upload_to(instance, filename):
    return 'compositealgos/{0}/{1}'.format(instance.pk, filename)


class CompositeAlgo(models.Model):
    """Storage Data table"""
    pkhash = models.CharField(primary_key=True, max_length=64, blank=True)
    file = models.FileField(upload_to=upload_to, max_length=500)  # path max length to 500 instead of default 100
    description = models.FileField(upload_to=upload_to, max_length=500)  # path max length to 500 instead of default 100
    validated = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """Use hash of file as primary key"""
        if not self.pkhash:
            self.pkhash = get_hash(self.file)
        super(CompositeAlgo, self).save(*args, **kwargs)

    def __str__(self):
        return f"CompositeAlgo with pkhash {self.pkhash} with validated {self.validated}"
