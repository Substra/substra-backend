import datetime
import contextlib
import os
import logging
import time


logger = logging.getLogger(__name__)


@contextlib.contextmanager
def lock_resource(resource_type: str, unique_identifier: str, ttl: int, delay: int = 0.02, timeout: int = 10):

    lock_filename = f"lock-{resource_type}-{unique_identifier}"
    lock_file = f"/tmp/{_make_filename_safe(lock_filename)}"

    def acquire_lock():
        try:
            fd = os.open(lock_file, os.O_CREAT | os.O_EXCL)
            os.close(fd)
            return True
        except FileExistsError:
            stat = os.stat(lock_file)
            creation_datetime = datetime.datetime.fromtimestamp(stat.st_mtime)
            expires_on = creation_datetime + datetime.timedelta(seconds=ttl)
            now = datetime.datetime.now()
            if expires_on < now:
                os.remove(lock_file)
                return acquire_lock()
            return False

    def release_lock():
        try:
            os.remove(lock_file)
        except FileNotFoundError:
            pass

    start = time.time()
    did_wait = False

    while not acquire_lock():
        if not did_wait:
            did_wait = True
            logger.debug(f"Lock: waiting for resource {lock_file} to be freed")
        if time.time() - start > timeout:
            raise Exception(f"Failed to acquire resource lock {unique_identifier} after {timeout} seconds")
        time.sleep(delay)

    if did_wait:
        logger.debug(f"Lock: Acquired resource {lock_file}")

    try:
        yield
    finally:
        release_lock()


def _make_filename_safe(filename: str) -> str:
    # https://stackoverflow.com/a/7406369/1370722
    return "".join([c for c in filename if c.isalpha() or c.isdigit() or c == " "]).rstrip()
