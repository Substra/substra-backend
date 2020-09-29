from django.conf import settings
import logging

BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
COLORS = {
    'WARNING': YELLOW,
    'INFO': None,
    'DEBUG': BLUE,
    'CRITICAL': RED,
    'ERROR': RED
}


class TaskFormatter(logging.Formatter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from celery._state import get_current_task
            self.get_current_task = get_current_task
        except ImportError:
            self.get_current_task = lambda: None

    def format(self, record):
        task = self.get_current_task()

        if settings.LOGGING_USE_COLORS:
            try:
                levelname = record.__dict__['levelname']
                color = COLORS[levelname]
                if color is not None:
                    record.__dict__.update(levelname=f'\033[0;{color+30}m{levelname}\033[0m')
            except Exception:
                pass  # Silently ignore coloring errors.

        if task and task.request and task.request.id:
            record.__dict__.update(task_id=f'[{task.request.id[0:8]}]')
        else:
            record.__dict__.setdefault('task_id', '')
        return super().format(record)
