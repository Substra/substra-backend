from django.db import models
from django.utils import timezone


class TimeStamped(models.Model):
    creation_date = models.DateTimeField(editable=False)
    last_modified = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        n = timezone.now()
        if not self.creation_date:
            self.creation_date = n

        self.last_modified = n
        return super(TimeStamped, self).save(*args, **kwargs)

    class Meta:
        abstract = True
