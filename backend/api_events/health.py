import tempfile

READY_FILE_PATH = f"{tempfile.gettempdir()}/ready"


class HealthService:
    def __init__(self):
        self._ready = False

    def ready(self) -> None:
        if not self._ready:
            _create_flag(READY_FILE_PATH)
        self._ready = True


def _create_flag(path):
    open(path, "a").close()
