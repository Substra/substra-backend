import contextlib
import os
import time
import uuid
from typing import Iterator
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)

LOCK_FILE_FOLDER = "/tmp"  # nosec
LOCK_FILE_PREFIX = "lock_"
SECONDARY_LOCK_FILE_PREFIX = "secondary_lock_"


@contextlib.contextmanager
def lock_resource(
    resource_type: str, unique_identifier: str, ttl: Optional[int] = None, delay: float = 0.02, timeout: int = 10
) -> Iterator[None]:
    """
    Acquire a lock on a resource.

    This function uses a file-based lock, so it will work within a container, but not across containers.
    For cross-container lock, we would need a database-based lock (Redis supports distributed locks with TTLs,
    PostgresSQL supports distributed locks without TTL).

    The function attempts to acquire the lock every `delay` seconds. If it fails to acquire the lock after `timeout`
    seconds, an error is raised.

    If `ttl` is specified, ensures the lock is kept for AT MOST `ttl` seconds, referred to as the lock TTL.
    If the lock TTL has expired, the lock file is deleted and the lock is released.

    We use a secondary lock to ensure only 1 process at a time can operate on the lock file.
    """

    slug = f"{resource_type}_{unique_identifier}"
    lock_file = _get_lock_file_path(slug)
    secondary_lock_file = _get_secondary_lock_file_path(slug)
    unique_id = str(uuid.uuid4())

    start = time.time()
    did_wait = False

    while not _try_acquire_lock(lock_file, secondary_lock_file, unique_id, ttl, delay, timeout):
        if not did_wait:
            did_wait = True
            logger.debug("Lock: Waiting for lock to be released", lock_file=lock_file)
        if time.time() - start > timeout:
            raise Exception(f"Failed to acquire lock after {timeout} seconds", lock_file=lock_file)
        time.sleep(delay)

    logger.debug("Lock: Acquired", lock_file=lock_file)

    try:
        yield
    finally:
        _release_lock(lock_file, secondary_lock_file, unique_id, delay, timeout)


def _try_acquire_lock(
    lock_file: str, secondary_lock_file: str, unique_id: str, ttl: Optional[int], delay: float, timeout: int
) -> bool:
    """
    Try to acquire the provided lock file.

    If the lock can be acquired, write the unique ID to it.

    If the lock cannot be acquired and `ttl` is set, check if the lock has expired. If it's the case, delete the lock
    file but don't acquire the lock.

    Return True if the lock has been acquired, else False.
    """
    try:
        fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        if ttl:
            _release_lock_if_expired(lock_file, secondary_lock_file, ttl, delay, timeout)
        return False
    else:
        os.write(fd, unique_id.encode())
        os.close(fd)
        return True


def _release_lock_if_expired(lock_file: str, secondary_lock_file: str, ttl: int, delay: float, timeout: int) -> None:
    """
    Check the lock file creation date to see if its TTL has expired. If so, delete the lock file.
    """
    with _acquire_secondary_lock(secondary_lock_file, delay, timeout):
        try:
            stat = os.stat(lock_file)
        except FileNotFoundError:
            # The lock file was removed by another process using _release_lock
            pass
        else:
            now = time.time()
            if stat.st_mtime + ttl < now:
                logger.exception(
                    (
                        "Releasing expired lock. "
                        "This means a process acquired the lock without releasing it properly/on time."
                    ),
                    lock_file=lock_file,
                )
                os.remove(lock_file)


def _release_lock(lock_file: str, secondary_lock_file: str, unique_id: str, delay: float, timeout: int) -> None:
    """
    Release the lock file if its unique_id matches the provided one.
    """
    with _acquire_secondary_lock(secondary_lock_file, delay, timeout):
        try:
            with open(lock_file, "r") as f:
                uuid = f.read()
            # Ensure we only remove the file _we_ created, not a file created by another caller
            if uuid == unique_id:
                os.remove(lock_file)
        except FileNotFoundError as e:
            logger.exception(
                "The lock file was removed by another process using _release_lock_if_expired",
                lock_file=lock_file,
                error=e,
            )
        except OSError as e:
            logger.exception("Error while releasing lock", lock_file=lock_file, error=e)


@contextlib.contextmanager
def _acquire_secondary_lock(secondary_lock_file: str, delay: float, timeout: float) -> None:
    """
    Acquire a lock on the lock file itself.

    Acquiring a lock on the lock file is useful because:

    - It ensures that only 1 process at a time can access/remove the lock file.
    - It ensures that operations on the lock file are canonical. Example operations:
      - "open followed by read followed by remove", see _release_lock()
      - "stat followed by remove", see _release_lock_if_expired()
    """
    try:
        start = time.time()
        while not _try_acquire_secondary_lock(secondary_lock_file):
            if time.time() - start > timeout:
                raise Exception(f"Failed to acquire secondary lock {secondary_lock_file} after {timeout} seconds")
            time.sleep(delay)
        yield
    finally:
        _release_secondary_lock(secondary_lock_file)


def _try_acquire_secondary_lock(secondary_lock_file: str) -> bool:
    """
    Try to acquire the provided secondary lock file.

    Return True if the lock has been acquired, else False.
    """
    try:
        fd = os.open(secondary_lock_file, os.O_CREAT | os.O_EXCL)
    except FileExistsError:
        return False
    else:
        os.close(fd)
        return True


def _release_secondary_lock(secondary_lock_file: str) -> None:
    """
    Remove the provided secondary lock file
    """
    os.remove(secondary_lock_file)


def _get_lock_file_path(slug: str) -> str:
    """
    Return the full path of the lock file
    """
    filename = _make_filename_safe(f"{LOCK_FILE_PREFIX}{slug}")
    return os.path.join(LOCK_FILE_FOLDER, filename)


def _get_secondary_lock_file_path(slug: str) -> str:
    """
    Return the full path of the secondary lock file.

    The secondary lock ensures only 1 process at a time can operate on the primary lock file.
    """
    filename = _make_filename_safe(f"{SECONDARY_LOCK_FILE_PREFIX}{slug}")
    return os.path.join(LOCK_FILE_FOLDER, filename)


def _make_filename_safe(filename: str) -> str:
    """
    Sanitize the input filename, which may include characters that are not allowed in a file path
    """
    keepcharacters = (" ", ".", "_")  # https://stackoverflow.com/a/7406369/1370722
    return "".join([c for c in filename if c.isalpha() or c.isdigit() or c in keepcharacters]).strip()
