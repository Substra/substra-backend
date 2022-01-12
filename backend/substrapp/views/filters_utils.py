import itertools
from urllib.parse import unquote

import structlog
from django.db.models import Q

from substrapp import exceptions

logger = structlog.get_logger(__name__)


FILTER_QUERIES = {
    "dataset": "query_datamanagers",
    "algo": "query_algos",
    "metric": "query_metrics",
    "model": "query_models",
}


def get_filters(query_params):
    """
    Transform user request search param in filters.

    >>> get_filters("algo:name:algo1")
    [
        {
            "algo": {
                "name": "algo1",
            },
        },
    ]

    >>> get_filters("algo:name:algo1,algo:owner:owner1")
    [
        {
            "algo": {
                "name": "algo1",
                "owner": "owner1",
            },
        },
    ]

    >>> get_filters("algo:name:algo1-OR-algo:owner:owner1")
    [
        {
            "algo": {
                "name": "algo1",
            },
        },
        {
            "algo": {
                "owner": "owner1",
            },
        },
    ]

    """
    filters = []
    groups = query_params.split("-OR-")

    for idx, group in enumerate(groups):

        # init
        filters.append({})

        # get number of subfilters and decode them
        subfilters = [unquote(x) for x in group.split(",")]

        for subfilter in subfilters:
            el = subfilter.split(":")
            # get parent
            parent = el[0]
            subparent = el[1]
            value = el[2]

            filter = {subparent: [unquote(value)]}

            if not len(filters[idx]):  # create and add it
                filters[idx] = {parent: filter}
            else:  # add it
                if parent in filters[idx]:  # add
                    if el[1] in filters[idx][parent]:  # concat in subparent
                        filters[idx][parent][subparent].extend([value])
                    else:  # add new subparent
                        filters[idx][parent].update(filter)
                else:  # create
                    filters[idx].update({parent: filter})

    return filters


def flatten_without_duplicates(list_of_list):
    res = []
    for item in itertools.chain.from_iterable(list_of_list):
        if item not in res:
            res.append(item)
    return res


def filter_list(object_type, data, query_params):
    """
    Filter django model instances by user request search param.
    """
    try:
        filters = get_filters(query_params)
    except Exception:
        raise exceptions.BadRequestError(f"Malformed search filters: invalid syntax: {query_params}")

    object_list = []

    for user_filter in filters:
        for filter_key, subfilters in user_filter.items():
            if not filter_key == object_type:
                raise exceptions.BadRequestError(
                    f"Malformed search filters: the filter {filter_key} should"
                    f"be the same as the object type {object_type}"
                )

            # Will be appended in object_list after being filtered
            filtered_list = data
            # Filter by own asset
            for attribute, val in subfilters.items():
                filtered_list = [x for x in filtered_list if x.get(attribute) in val]

            object_list.append(filtered_list)

    return flatten_without_duplicates(object_list)


def filter_queryset(object_type, queryset, query_params, mapping_callback=None):
    """
    Filter django model queryset by user request search param.
    Provide a `mapping_callback` to customize filter key and/or values.

    >>> filter_queryset("algo", Algo.objects, "algo:name:algo1")
    Algo.objects.filter(Q(name="algo1"))

    >>> filter_queryset("algo", Algo.objects, "algo:name:algo1,algo:owner:owner1")
    Algo.objects.filter(Q(name="algo1") & Q(owner="owner1"))

    >>> filter_queryset("algo", Algo.objects, "algo:name:algo1-OR-algo:owner:owner1")
    Algo.objects.filter(Q(name="algo1") | Q(owner="owner1"))

    >>> def map_category(key, values):
    ...     if key == "category":
    ...         values = [algo_pb2.AlgoCategory.Value(value) for value in values]
    ...     return key, values

    >>> filter_queryset("algo", Algo.objects, "algo:category:ALGO_SIMPLE", map_category)
    Algo.objects.filter(Q(category=1))

    """
    try:
        filters = get_filters(query_params)
    except Exception:
        raise exceptions.BadRequestError(f"Malformed search filters: invalid syntax: {query_params}")

    or_params = None
    for or_filter in filters:
        and_params = None
        for key, values in or_filter[object_type].items():
            if mapping_callback is not None:
                key, values = mapping_callback(key, values)
            # handle multi-values
            if len(values) == 1:
                param = Q(**{key: values[0]})
            else:
                param = Q(**{f"{key}__in": values})
            and_params = param if and_params is None else and_params & param
        or_params = and_params if or_params is None else or_params | and_params

    return queryset.filter(or_params)
