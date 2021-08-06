# encoding: utf-8

from __future__ import unicode_literals, absolute_import
from rest_framework.pagination import PageNumberPagination
from django.conf import settings


REALLY_BIG_INT = 2**32


class DefaultPageNumberPagination(PageNumberPagination):
    max_page_size = getattr(settings, 'PAGINATION_MAX_PAGE_SIZE', 100)
    page_size_query_param = "page_size"
    page_size = REALLY_BIG_INT  # Default is a paginated response with all data in 1 page


class PaginationMixin:
    def paginate_response(self, data, status):
        data_for_one_page = self.paginate_queryset(data)
        if data_for_one_page is None:
            raise Exception("Failed to build a chunk of data for 1 page.\
 Hint: PaginationMixin is expected to be used in conjunction with DefaultPageNumberPagination")

        return self.get_paginated_response(data_for_one_page)
