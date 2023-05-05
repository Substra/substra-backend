from django.conf import settings

# In the effort to decouple substrapp from django, we re-implement some utils from Django
TASK_PROFILING_BASE_URL = settings.DEFAULT_DOMAIN + "/task_profiling/"


def _join_url(prefix: str, suffix: str) -> str:
    return f"{prefix}{suffix}/"


def get_task_profiling_detail_url(profiling_key: str) -> str:
    """Get URL for a specific profiling"""

    return _join_url(TASK_PROFILING_BASE_URL, profiling_key)


def get_task_profiling_steps_base_url(profiling_key: str) -> str:
    """Get URL for steps list for a specific profiling"""
    profiling_detail_url = get_task_profiling_detail_url(profiling_key)
    return _join_url(profiling_detail_url, "step")
