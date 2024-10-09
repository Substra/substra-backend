from django.conf import settings


# In the effort to decouple substrapp from django, we re-implement some utils from Django
def _join_url(prefix: str, suffix: str) -> str:
    return f"{prefix}{suffix}/"


def get_task_profiling_detail_url(profiling_key: str) -> str:
    """Get URL for a specific profiling"""
    task_list_url = _join_url(settings.DEFAULT_DOMAIN, "/task")
    task_detail_url = _join_url(task_list_url, profiling_key)
    return _join_url(task_detail_url, "profiling")


def get_task_profiling_steps_base_url(profiling_key: str) -> str:
    """Get URL for steps list for a specific profiling"""
    profiling_detail_url = get_task_profiling_detail_url(profiling_key)
    return _join_url(profiling_detail_url, "step")


def get_task_profiling_steps_detail_url(profiling_key: str, step_key: str) -> str:
    """Get URL for steps list for a specific step"""
    base_step_url = get_task_profiling_steps_base_url(profiling_key)
    return _join_url(base_step_url, step_key)
