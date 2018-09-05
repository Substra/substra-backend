from substrapp.utils import compute_hash


def get_hash(fileobj):
    openedfile = fileobj.open()  # do not autoclose file, otherwise, you won't be able to register the models.FileField
    block = openedfile.read()

    return compute_hash(block)
