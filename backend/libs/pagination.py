from django.conf import settings
from rest_framework.pagination import PageNumberPagination

from substrapp.views.utils import ApiResponse

REALLY_BIG_INT = 2 ** 32


class DefaultPageNumberPagination(PageNumberPagination):
    max_page_size = getattr(settings, "PAGINATION_MAX_PAGE_SIZE", 100)
    page_size_query_param = "page_size"
    page_size = REALLY_BIG_INT  # Default is a paginated response with all data in 1 page


class PaginationMixin:
    def paginate_response(self, data):
        data_for_one_page = self.paginate_queryset(data)
        if data_for_one_page is None:
            raise Exception(
                "Failed to build a chunk of data for 1 page. "
                "Hint: PaginationMixin is expected to be used in conjunction with DefaultPageNumberPagination"
            )
        response = self.get_paginated_response(data_for_one_page)
        return ApiResponse.add_content_disposition_header(response)

    def is_page_size_param_present(self):
        page_size = self.request.query_params.get(DefaultPageNumberPagination.page_size_query_param)
        return page_size is not None
