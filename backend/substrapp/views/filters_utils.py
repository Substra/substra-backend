import logging
from urllib.parse import unquote

from substrapp.ledger_utils import query_ledger
from substrapp import exceptions

logger = logging.getLogger(__name__)


FILTER_QUERIES = {
    'dataset': 'queryDataManagers',
    'algo': 'queryAlgos',
    'objective': 'queryObjectives',
    'model': 'queryModels',
    'composite_algo': 'queryCompositeAlgos',
    'aggregate_algo': 'queryAggregateAlgos'
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

    Where "attribute" is actually an attribute of the model's traintuple or compositeTraintuple (depending on its type).
    """

    if 'compositeTraintuple' in model:
        return model['compositeTraintuple']
    elif 'aggregatetuple' in model:
        return model['aggregatetuple']
    elif 'traintuple' in model:
        return model['traintuple']
    else:
        raise NotImplementedError


def filter_list(object_type, data, query_params):
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
                            filtered_list = [x for x in filtered_list if x[attribute]['name'] in val]
                        else:
                            filtered_list = [x for x in filtered_list if x[attribute] in val]

                else:
                    for attribute, val in subfilters.items():
                        filtered_list = [x for x in filtered_list if x.get(attribute) in val]
            else:
                # Filter by other asset

                # Get other asset list
                filtering_data = query_ledger('mychannel', fcn=FILTER_QUERIES[filter_key], args=[])

                filtering_data = filtering_data if filtering_data else []

                if filter_key in ('algo', 'composite_algo', 'aggregate_algo'):
                    for attribute, val in subfilters.items():
                        filtering_data = [x for x in filtering_data if x[attribute] in val]
                        hashes = [x['key'] for x in filtering_data]

                        if object_type == 'model':
                            filtered_list = [x for x in filtered_list
                                             if _get_model_tuple(x)['algo']['hash'] in hashes]

                elif filter_key == 'model':
                    for attribute, val in subfilters.items():
                        filtering_data = [
                            x for x in filtering_data
                            if (
                                (
                                    _get_model_tuple(x).get('outModel') and
                                    _get_model_tuple(x)['outModel'][attribute] in val
                                ) or (
                                    _get_model_tuple(x).get('outTrunkModel') and
                                    _get_model_tuple(x)['outTrunkModel']['outModel'][attribute] in val
                                ) or (
                                    _get_model_tuple(x).get('outHeadModel') and
                                    _get_model_tuple(x)['outHeadModel']['outModel'][attribute] in val
                                )
                            )
                        ]

                        if object_type in ['algo', 'composite_algo', 'aggregatealgo']:
                            hashes = [_get_model_tuple(x)['algo']['hash'] for x in filtering_data]
                            filtered_list = [x for x in filtered_list if x['key'] in hashes]

                        elif object_type == 'dataset':
                            hashes = []
                            for x in filtering_data:
                                try:
                                    hashes.append(x['testtuple']['dataset']['openerHash'])
                                except KeyError:
                                    pass
                                try:
                                    hashes.append(_get_model_tuple(x)['dataset']['openerHash'])
                                except KeyError:
                                    pass

                            filtered_list = [
                                x for x in filtered_list
                                if x['opener']['hash'] in hashes
                            ]

                        elif object_type == 'objective':
                            hashes = [
                                x['testtuple']['objective']['hash'] for x in filtering_data
                                if x['testtuple'] and x['testtuple']['objective']
                            ]
                            filtered_list = [x for x in filtered_list if x['key'] in hashes]

                elif filter_key == 'dataset':
                    for attribute, val in subfilters.items():
                        filtering_data = [x for x in filtering_data if x[attribute] in val]
                        hashes = [x['key'] for x in filtering_data]

                        if object_type == 'model':
                            filtered_list = [x for x in filtered_list
                                             if _get_model_tuple(x).get('dataset', {}).get('openerHash') in hashes]
                        elif object_type == 'objective':
                            objective_keys = [x['objectiveKey'] for x in filtering_data]
                            filtered_list = [x for x in filtered_list
                                             if x['key'] in objective_keys or
                                             (x['testDataset'] and x['testDataset']['dataManagerKey'] in hashes)]

                elif filter_key == 'objective':
                    for attribute, val in subfilters.items():
                        if attribute == 'metrics':  # specific to nested metrics
                            filtering_data = [x for x in filtering_data if x[attribute]['name'] in val]
                        else:
                            filtering_data = [x for x in filtering_data if x[attribute] in val]

                        hashes = [x['key'] for x in filtering_data]

                        if object_type == 'model':
                            filtered_list = [
                                x for x in filtered_list
                                if (x['testtuple'] and x['testtuple']['objective'] and
                                    x['testtuple']['objective']['hash'] in hashes)
                            ]
                        elif object_type == 'dataset':
                            filtered_list = [x for x in filtered_list
                                             if x['objectiveKey'] in hashes]

            object_list.append(filtered_list)

    return object_list
