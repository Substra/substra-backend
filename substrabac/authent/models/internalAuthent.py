from django.db import models

from authent.models.permission import Permission


class InternalAuthent(models.Model):
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    creator = models.CharField(max_length=64)

    def __str__(self):
        return f'internal authent with permission {self.permission.name} and creator {self.creator}'
