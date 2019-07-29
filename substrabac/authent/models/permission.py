from django.db import models


class Permission(models.Model):
    name = models.CharField(primary_key=True, max_length=256, blank=True)

    def __str__(self):
        return self.name
