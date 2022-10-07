import abc
import json

import structlog
from django.db.models import Q
from django.forms import CharField
from django.forms import ChoiceField
from django.forms import UUIDField
from django_filters.rest_framework import BaseInFilter
from django_filters.rest_framework import CharFilter
from django_filters.rest_framework import ChoiceFilter
from django_filters.rest_framework import UUIDFilter
from rest_framework.filters import BaseFilterBackend
from rest_framework.filters import SearchFilter

from backend.settings.common import to_bool

logger = structlog.get_logger(__name__)


class PermissionFilter(BaseFilterBackend):
    """Filter assets who can be used by a given set of organizations"""

    def get_param(self):
        try:
            return self.param
        except AttributeError:
            raise NotImplementedError("Missing param definition")

    def get_field(self):
        try:
            return self.field
        except AttributeError:
            raise NotImplementedError("Missing field definition")

    def get_organization_ids(self, request):
        params = request.query_params.get(self.get_param())
        if params:
            organization_ids = [param.strip() for param in params.split(",")]
            return organization_ids
        return []

    def filter_queryset(self, request, queryset, view):
        organization_ids = self.get_organization_ids(request)
        if organization_ids:
            is_public = Q(**{f"{self.get_field()}_public": True})
            is_authorized = Q(**{f"{self.get_field()}_authorized_ids__contains": organization_ids})
            queryset = queryset.filter(is_public | is_authorized)
        return queryset


class ProcessPermissionFilter(PermissionFilter):
    param = "can_process"
    field = "permissions_process"


class LogsPermissionFilter(PermissionFilter):
    param = "can_access_logs"
    field = "logs_permission"


class MatchFilter(SearchFilter):
    """Full text search in a selected number of fields.

    Searches by default in key and name.
    The list can be customized through the search_fields attribute on the view."""

    search_param = "match"
    default_search_fields = ("key", "name")

    def get_search_fields(self, view, request):
        return getattr(view, "search_fields", self.default_search_fields)


class ChoiceInFilter(BaseInFilter, ChoiceFilter):
    """Allow choice field to be filtered with IN lookup passing comma separated values list"""

    field_class = ChoiceField


class CharInFilter(BaseInFilter, CharFilter):
    """Allow char field to be filtered with IN lookup passing comma separated values list"""

    field_class = CharField


class UUIDInFilter(BaseInFilter, UUIDFilter):
    """Allow uuid field to be filtered with IN lookup passing comma separated values list"""

    field_class = UUIDField


class MetadataFilterBackend(BaseFilterBackend):
    """Accepts filters that will match values in the metadata field.

    * The query param value must be a JSON encoded string.
    * The decoded query param value must be an array where each item is defined as:
    {
        "key": str # the key of the metadata to filter on
        "type": "is", "contains" or "exists" # the type of query that will be used
        "value": str # the value that the key must be (if type is "is") or contain (if type if "contains")
    }

    All values will be cast as string.

    If the query param value isn't in the right format, it'll be ignored entirely.
    """

    @abc.abstractmethod
    def _apply_filters(self, queryset, filter_keys):
        raise NotImplementedError("Method not implemented!")

    def filter_queryset(self, request, queryset, view):
        metadata = request.query_params.get("metadata")
        filters = []
        try:
            metadata = json.loads(metadata)
            for f in metadata:
                filters.append({"key": str(f["key"]), "type": str(f["type"]), "value": str(f.get("value", ""))})
        except (TypeError, KeyError, json.JSONDecodeError):
            return queryset

        if not filters:
            return queryset

        # split filters by type
        exists_filters = [f for f in filters if f["type"] == "exists"]
        is_filters = [f for f in filters if f["type"] == "is"]
        contains_filters = [f for f in filters if f["type"] == "contains"]

        # cast values we want to filter on as strings
        filter_keys = [f["key"] for f in is_filters + contains_filters]
        # table_name = queryset.first()._meta.db_table
        queryset = self._apply_filters(queryset, filter_keys)

        # convert filters into django filters
        django_filters = {}
        if exists_filters:
            django_filters["metadata__has_keys"] = [f["key"] for f in exists_filters]
        for f in is_filters:
            django_filters[f'metadata_filters__{f["key"]}'] = f["value"]
        for f in contains_filters:
            django_filters[f'metadata_filters__{f["key"]}__icontains'] = f["value"]

        return queryset.filter(**django_filters)
