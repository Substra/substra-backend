import structlog
import itertools

from urllib.parse import unquote
from substrapp import exceptions

logger = structlog.get_logger(__name__)


FILTER_QUERIES = {
    'dataset': 'query_datamanagers',
    'algo': 'query_algos',
    'metric': 'query_metrics',
    'model': 'query_models',
}


def get_filters(query_params):
    filters = []
    groups = query_params.split('-OR-')

    for idx, group in enumerate(groups):

        # init
        filters.append({})

        # get number of subfilters and decode them
        subfilters = [unquote(x) for x in group.split(',')]

        for subfilter in subfilters:
            el = subfilter.split(':')
            # get parent
            parent = el[0]
            subparent = el[1]
            value = el[2]

            filter = {
                subparent: [unquote(value)]
            }

            if not len(filters[idx]):  # create and add it
                filters[idx] = {
                    parent: filter
                }
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
        filter object type by its parameters
    """
    try:
        filters = get_filters(query_params)
    except Exception:
        # TODO add better filters parsing to avoid this catch all
        message = f'Malformed search filters: invalid syntax: {query_params}'
        logger.exception(message)
        raise exceptions.BadRequestError(message)

    object_list = []

    for user_filter in filters:
        for filter_key, subfilters in user_filter.items():
            if not filter_key == object_type:
                raise exceptions.BadRequestError(
                    f'Malformed search filters: the filter {filter_key} should'
                    f'be the same as the object type {object_type}')

            # Will be appended in object_list after being filtered
            filtered_list = data
            # Filter by own asset
            for attribute, val in subfilters.items():
                filtered_list = [x for x in filtered_list if x.get(attribute) in val]

            object_list.append(filtered_list)

    return flatten_without_duplicates(object_list)
