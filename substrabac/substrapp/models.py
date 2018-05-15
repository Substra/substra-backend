import hashlib
from django.db import models


CHUNKSIZE = 4096


def hash_upload(fileobj):
    """
    Returns the hash of a file
    """
    openedfile = fileobj.open()
    sha256_hash = hashlib.sha256()
    # Read and update hash string value in blocks of 4K
    for byte_block in iter(lambda: openedfile.read(CHUNKSIZE), ""):
        sha256_hash.update(byte_block.encode())
    return sha256_hash.hexdigest()


class Problem(models.Model):
    """Storage Problem table"""
    pkhash = models.CharField(primary_key=True, max_length=64, blank=True)
    validated = models.BooleanField(default=False, blank=True)
    description = models.FileField()
    metrics = models.FileField()

    def save(self, *args, **kwargs):
        """Use hash of description file as primary key"""
        if not self.pkhash:
            self.pkhash = hash_upload(self.description)
        super(Problem, self).save(*args, **kwargs)

    def __str__(self):
        return "%s %s" % (self.pkhash, self.validated)


class DataOpener(models.Model):
    """Storage DataOpener table"""
    pkhash = models.CharField(primary_key=True, max_length=64, blank=True)
    name = models.CharField(blank=True, max_length=24)
    script = models.FileField()

    def save(self, *args, **kwargs):
        """Use hash of description file as primary key"""
        if not self.pkhash:
            self.pkhash = hash_upload(self.script)
        super(DataOpener, self).save(*args, **kwargs)

    def __str__(self):
        return "%s %s" % (self.pkhash, self.name)


class Data(models.Model):
    """Storage Data table"""
    pkhash = models.CharField(primary_key=True, max_length=64, blank=True)
    validated = models.BooleanField(default=False)
    features = models.FileField()
    labels = models.FileField()

    def save(self, *args, **kwargs):
        """Use hash of description file as primary key"""
        if self.pkhash is None:
            self.pkhash = hash_upload(self.features)
        super(Data, self).save(*args, **kwargs)

    def __str__(self):
        return "%s %s" % (self.pkhash, self.validated)
