from django.conf import settings
from rest_framework.pagination import PageNumberPagination

REALLY_BIG_INT = 2**32


class DefaultPageNumberPagination(PageNumberPagination):
    max_page_size = getattr(settings, "PAGINATION_MAX_PAGE_SIZE", 10000)
    page_size_query_param = "page_size"
    page_size = REALLY_BIG_INT  # Default is a paginated response with all data in 1 page
