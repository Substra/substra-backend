import hashlib

CHUNKSIZE = 4096


def compute_hash(fileobj):
    """
    Returns the hash of a file
    """
    openedfile = fileobj.open()
    sha256_hash = hashlib.sha256()
    # Read and update hash string value in blocks of 4K
    for byte_block in iter(lambda: openedfile.read(CHUNKSIZE), ""):
        sha256_hash.update(byte_block.encode())
    return sha256_hash.hexdigest()
