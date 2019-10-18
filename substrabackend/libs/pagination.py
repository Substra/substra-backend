# encoding: utf-8

from __future__ import unicode_literals, absolute_import
from rest_framework.pagination import PageNumberPagination


class LimitedPagination(PageNumberPagination):
    page_size = 30
    max_page_size = 10000
