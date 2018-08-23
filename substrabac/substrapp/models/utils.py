import hashlib

CHUNKSIZE = 4096


def compute_hash(fileobj):
    """
    Returns the hash of a file
    """
    sha256_hash = hashlib.sha256()

    with fileobj.open() as openedfile:
        block = openedfile.read()

    if isinstance(block, str):
        block = block.encode()
    sha256_hash.update(block)

    return sha256_hash.hexdigest()
