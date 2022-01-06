import contextlib
import os
import time
import uuid

import structlog

logger = structlog.get_logger(__name__)

LOCK_FILE_FOLDER = "/tmp"  # nosec
LOCK_FILE_PREFIX = "lock_"
LOCK_FILE_PREFIX_UNLINK = "unlink_lock_"


# TODO: 'lock_resource' is too complex, consider refactoring
@contextlib.contextmanager  # noqa: C901
def lock_resource(  # noqa: C901
    resource_type: str, unique_identifier: str, ttl: int, delay: int = 0.02, timeout: int = 10
):
    """
    Acquire a lock on a resource.

    This function uses a file-based lock, so it will work within a container, but not across containers.
    For cross-container lock, we would need a database-based lock (Redis supports distributed locks with TTLs)

    Ensures the lock is kept for AT MOST `timeout` seconds, referred to as the lock TTL.
    If the lock TTL has expired, the lock file is deleted and the lock is released.

    If you're thinking of modifying this function, make sure you have time ahead of you -_-
    """

    slug = f"{resource_type}_{unique_identifier}"

    lock_filename = _make_filename_safe(f"{LOCK_FILE_PREFIX}{slug}")
    unlink_lock_filename = _make_filename_safe(f"{LOCK_FILE_PREFIX_UNLINK}{slug}")

    lock_file = os.path.join(LOCK_FILE_FOLDER, lock_filename)
    unlink_lock_file = os.path.join(LOCK_FILE_FOLDER, unlink_lock_filename)

    unique_id = str(uuid.uuid4())

    def acquire_lock():
        try:
            fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            check_lock_file_ttl()
            return False
        else:
            os.write(fd, unique_id.encode())
            os.close(fd)
            return True

    def check_lock_file_ttl():
        """
        Check the lock file creation date to see if its TTL has expired. If so, delete the lock file.
        """
        # ensure only 1 process at a time read/remove the lock file
        with _unlink_lock(unlink_lock_file, delay, timeout):
            try:
                stat = os.stat(lock_file)
            except FileNotFoundError:
                # lock file was removed by another process
                pass
            else:
                now = time.time()
                if stat.st_mtime + ttl < now:
                    os.remove(lock_file)

    def release_lock():
        # ensure only 1 process at a time read/remove the lock file
        with _unlink_lock(unlink_lock_file, delay, timeout):
            try:
                with open(lock_file, "r") as f:
                    uuid = f.read()
                # ensure we only remove the file _we_ created, not a file created by another caller
                if uuid == unique_id:
                    os.remove(lock_file)
            except Exception:  # nosec
                pass

    start = time.time()
    did_wait = False

    while not acquire_lock():
        if not did_wait:
            did_wait = True
            logger.debug("Lock: waiting for resource to be freed", lock_file=lock_file)
        if time.time() - start > timeout:
            raise Exception(f"Failed to acquire resource lock {unique_identifier} after {timeout} seconds")
        time.sleep(delay)

    logger.debug("Lock: Acquired resource", lock_file=lock_file)

    try:
        yield
    finally:
        release_lock()


def _make_filename_safe(filename: str) -> str:
    # https://stackoverflow.com/a/7406369/1370722
    keepcharacters = (" ", ".", "_")
    return "".join([c for c in filename if c.isalpha() or c.isdigit() or c in keepcharacters]).strip()


@contextlib.contextmanager
def _unlink_lock(ttl_lock_file: str, delay: float, timeout: float):
    def acquire():
        start = time.time()
        while not try_acquire_lock():
            if time.time() - start > timeout:
                raise Exception(f"Failed to acquire resource unlink lock {ttl_lock_file} after {timeout} seconds")
            time.sleep(delay)

    def try_acquire_lock():
        try:
            fd = os.open(ttl_lock_file, os.O_CREAT | os.O_EXCL)
        except FileExistsError:
            pass
        else:
            os.close(fd)
            return True

        return False

    def release():
        os.remove(ttl_lock_file)

    try:
        acquire()
        yield
    finally:
        release()
