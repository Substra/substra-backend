from django.conf import settings
from django.urls import reverse

from substrapp.utils.url import TASK_PROFILING_BASE_URL
from substrapp.utils.url import get_task_profiling_detail_url
from substrapp.utils.url import get_task_profiling_steps_base_url


# We still rely on Django for testing the url
def test_task_profiling_base_url():
    django_url = settings.DEFAULT_DOMAIN + reverse("api:task_profiling-list")
    substrapp_url = TASK_PROFILING_BASE_URL

    assert django_url == substrapp_url


def test_task_profiling_detail_url():
    profiling_key = "1"
    django_url = settings.DEFAULT_DOMAIN + reverse("api:task_profiling-detail", args=[profiling_key])
    substrapp_url = get_task_profiling_detail_url(profiling_key)

    assert django_url == substrapp_url


def test_task_profiling_steps_base_url():
    profiling_key = "1"
    django_url = settings.DEFAULT_DOMAIN + reverse("api:step-list", args=[profiling_key])
    substrapp_url = get_task_profiling_steps_base_url(profiling_key)

    assert django_url == substrapp_url
