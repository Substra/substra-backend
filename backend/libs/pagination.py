from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class DefaultPageNumberPagination(PageNumberPagination):
    max_page_size = getattr(settings, "PAGINATION_MAX_PAGE_SIZE", 1000)
    page_size_query_param = "page_size"
    page_size = 100  # Default is a paginated response with 100 items per page


class LargePageNumberPagination(PageNumberPagination):
    max_page_size = getattr(settings, "PAGINATION_MAX_PAGE_SIZE", 10000)
    page_size_query_param = "page_size"
    page_size = 1000


class SmallPageNumberPagination(PageNumberPagination):
    max_page_size = getattr(settings, "PAGINATION_MAX_PAGE_SIZE", 100)
    page_size_query_param = "page_size"
    page_size = 10
