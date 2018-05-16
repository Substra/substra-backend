import hashlib

CHUNKSIZE = 4096


def compute_hash(fileobj):
    """
    Returns the hash of a file
    """
    openedfile = fileobj.open()
    sha256_hash = hashlib.sha256()
    block = openedfile.read()
    if isinstance(block, str):
        block = block.encode()
    sha256_hash.update(block)
    # Read and update hash string value in blocks of 4K
    # for block in iter(lambda: openedfile.read(CHUNKSIZE), ""):
    #     print('yo')
    #     # if isinstance(block, str):
    #     #     print('yo')
    #     #    block = block.encode()
    #     sha256_hash.update(block.encode())
    return sha256_hash.hexdigest()
