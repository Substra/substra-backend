import logging
import itertools

from urllib.parse import unquote

from substrapp.orchestrator.api import get_orchestrator_client
from substrapp import exceptions
from substrapp.views.utils import ALGO_CATEGORY

logger = logging.getLogger(__name__)


FILTER_QUERIES = {
    'dataset': 'query_datamanagers',
    'algo': 'query_algos',
    'objective': 'query_objectives',
    'model': 'query_models',
    'composite_algo': 'query_algos',
    'aggregate_algo': 'query_algos',
}

AUTHORIZED_FILTERS = {
    'compute_plan': ['compute_plan'],
    'dataset': ['dataset', 'model', 'objective'],
    'algo': ['model', 'algo', 'composite_algo', 'aggregate_algo'],
    'composite_algo': ['composite_algo', 'algo', 'aggregate_algo', 'model'],
    'aggregate_algo': ['aggregate_algo', 'algo', 'composite_algo', 'model'],
    'objective': ['model', 'dataset', 'objective'],
    'model': ['model', 'algo', 'composite_algo', 'aggregate_algo', 'dataset', 'objective'],
    'traintuple': ['traintuple'],
    'testtuple': ['testtuple'],
    'composite_traintuple': ['composite_traintuple'],
    'aggregatetuple': ['aggregatetuple'],
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


def _same_nature(filter_key, object_type):
    if filter_key == object_type:
        return True

    # algo and composite algos are of the same nature
    return {filter_key, object_type} <= {'algo', 'composite_algo', 'aggregate_algo'}


def _get_model_tuple(model):
    """
    Return the correct part of a model to use for filtering.

    This is necessary because the API allows to filter models using this syntax:

        model:attribute:value

    Where "attribute" is actually an attribute of the model's traintuple or
    composite_traintuple (depending on its type).
    """

    if 'composite_traintuple' in model:
        return model['composite_traintuple']
    elif 'aggregatetuple' in model:
        return model['aggregatetuple']
    elif 'traintuple' in model:
        return model['traintuple']
    else:
        raise NotImplementedError


def flatten_without_duplicates(list_of_list):
    res = []
    for item in itertools.chain.from_iterable(list_of_list):
        if item not in res:
            res.append(item)
    return res


def filter_list(channel_name, object_type, data, query_params):
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

            if filter_key not in AUTHORIZED_FILTERS[object_type]:
                raise exceptions.BadRequestError(
                    f'Malformed search filters: not authorized filter key {filter_key} for asset {object_type}')

            # Will be appended in object_list after been filtered
            filtered_list = data

            if _same_nature(filter_key, object_type):
                # Filter by own asset
                if filter_key == 'model':
                    for attribute, val in subfilters.items():
                        filtered_list = [x for x in filtered_list if _get_model_tuple(x).get(attribute) in val]
                elif filter_key == 'objective':
                    for attribute, val in subfilters.items():
                        if attribute == 'metrics':  # specific to nested metrics
                            filtered_list = [x for x in filtered_list if x['metrics_name'] in val]
                        else:
                            filtered_list = [x for x in filtered_list if x[attribute] in val]

                else:
                    for attribute, val in subfilters.items():
                        filtered_list = [x for x in filtered_list if x.get(attribute) in val]
            else:
                # Filter by other asset

                # Get other asset list
                with get_orchestrator_client(channel_name) as client:
                    if filter_key in ['algo', 'composite_algo', 'aggregate_algo']:
                        filtering_data = getattr(client, FILTER_QUERIES[filter_key])(ALGO_CATEGORY[filter_key])
                    else:
                        filtering_data = getattr(client, FILTER_QUERIES[filter_key])()

                filtering_data = filtering_data if filtering_data else []

                if filter_key in ('algo', 'composite_algo', 'aggregate_algo'):
                    for attribute, val in subfilters.items():
                        filtering_data = [x for x in filtering_data if x[attribute] in val]
                        keys = [x['key'] for x in filtering_data]
                        if object_type == 'model':
                            filtered_list = [x for x in filtered_list
                                             if _get_model_tuple(x)['algo']['key'] in keys]

                elif filter_key == 'model':
                    for attribute, val in subfilters.items():
                        filtering_data = [
                            x for x in filtering_data
                            if (
                                (
                                    _get_model_tuple(x).get('out_model') and
                                    _get_model_tuple(x)['out_model'][attribute] in val
                                ) or (
                                    _get_model_tuple(x).get('out_trunk_model') and
                                    _get_model_tuple(x)['out_trunk_model'].get('out_model') and
                                    _get_model_tuple(x)['out_trunk_model']['out_model'][attribute] in val
                                ) or (
                                    _get_model_tuple(x).get('out_head_model') and
                                    _get_model_tuple(x)['out_head_model'].get('out_model') and
                                    _get_model_tuple(x)['out_head_model']['out_model'][attribute] in val
                                )
                            )
                        ]

                        if object_type in ['algo', 'composite_algo', 'aggregate_algo']:
                            keys = [_get_model_tuple(x)['algo']['key'] for x in filtering_data]
                            filtered_list = [x for x in filtered_list if x['key'] in keys]

                        elif object_type == 'dataset':
                            checksums = []
                            for x in filtering_data:
                                try:
                                    checksums.append(x['testtuple']['dataset']['opener_checksum'])
                                except KeyError:
                                    pass
                                try:
                                    checksums.append(_get_model_tuple(x)['dataset']['opener_checksum'])
                                except KeyError:
                                    pass

                            filtered_list = [
                                x for x in filtered_list
                                if x['opener']['checksum'] in checksums
                            ]

                        elif object_type == 'objective':
                            keys = [
                                x['testtuple']['objective']['key'] for x in filtering_data
                                if x['testtuple'] and x['testtuple']['objective']
                            ]
                            filtered_list = [x for x in filtered_list if x['key'] in keys]

                elif filter_key == 'dataset':
                    for attribute, val in subfilters.items():
                        filtering_data = [x for x in filtering_data if x[attribute] in val]
                        keys = [x['key'] for x in filtering_data]
                        if object_type == 'model':
                            filtered_list = [x for x in filtered_list
                                             if _get_model_tuple(x).get('dataset', {}).get('key', '') in keys]
                        elif object_type == 'objective':
                            objective_keys = [x['objective_key'] for x in filtering_data]
                            filtered_list = [x for x in filtered_list
                                             if x['key'] in objective_keys or
                                             (x['data_manager_key'] and x['data_manager_key'] in keys)]

                elif filter_key == 'objective':
                    for attribute, val in subfilters.items():
                        if attribute == 'metrics':  # specific to nested metrics
                            filtering_data = [x for x in filtering_data if x['metrics_name'] in val]
                        else:
                            filtering_data = [x for x in filtering_data if x[attribute] in val]

                        keys = [x['key'] for x in filtering_data]

                        if object_type == 'model':
                            filtered_list = [
                                x for x in filtered_list
                                if (x['testtuple'] and x['testtuple']['objective'] and
                                    x['testtuple']['objective']['key'] in keys)
                            ]
                        elif object_type == 'dataset':
                            filtered_list = [x for x in filtered_list
                                             if x['objective_key'] in keys]

            object_list.append(filtered_list)

    return flatten_without_duplicates(object_list)
