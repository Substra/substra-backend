from django.db import models

from authent.models.permission import Permission


class InternalAuthent(models.Model):
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    modulus = models.CharField(max_length=64)

    def __str__(self):
        # TODO
        return self.permission.name
