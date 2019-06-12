# encoding: utf-8

from django.core.exceptions import MiddlewareNotUsed
from django.conf import settings
from django.db import connection


"""
Originally code was taken from http://djangosnippets.org/snippets/290/
But I was made some improvements like:
- print URL from what queries was
- don't show queries from static URLs (MEDIA_URL and STATIC_URL, also for /favicon.ico).
- If DEBUG is False tell to django to not use this middleware
- Remove guessing of terminal width (This breaks the rendered SQL)
"""


class SQLPrintingMiddleware:
    """
    Middleware which prints out a list of all SQL queries done
    for each view that is processed. This is only useful for debugging.
    """

    def __init__(self, get_response):
        if not settings.DEBUG:
            raise MiddlewareNotUsed

        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        response = self.get_response(request)

        if (len(connection.queries) == 0 or
                request.path_info.startswith('/favicon.ico') or
                request.path_info.startswith(settings.STATIC_URL) or
                request.path_info.startswith(settings.MEDIA_URL)):
            return response

        indentation = 2
        print(("\n\n%s\033[1;35m[SQL Queries for]\033[1;34m %s\033[0m\n" % (" " * indentation, request.path_info)))
        total_time = 0.0
        for query in connection.queries:
            if query['sql']:
                nice_sql = query['sql'].replace('"', '').replace(',', ', ')
                sql = "\033[1;31m[%s]\033[0m %s" % (query['time'], nice_sql)
                total_time = total_time + float(query['time'])
                print(("%s%s\n" % (" " * indentation, sql)))
        replace_tuple = (" " * indentation, str(total_time), str(len(connection.queries)))
        print(("%s\033[1;32m[TOTAL TIME: %s seconds (%s queries)]\033[0m" % replace_tuple))
        return response
