from urllib.parse import unquote

from substrapp.ledger_utils import query_ledger


FILTER_QUERIES = {
    'dataset': 'queryDataManagers',
    'algo': 'queryAlgos',
    'objective': 'queryObjectives',
    'model': 'queryTraintuples',
    'composite_algo': 'queryCompositeAlgos'
}

AUTHORIZED_FILTERS = {
    'dataset': ['dataset', 'model', 'objective'],
    'algo': ['model', 'algo', 'composite_algo'],
    'composite_algo': ['composite_algo', 'algo', 'model'],
    'objective': ['model', 'dataset', 'objective'],
    'model': ['model', 'algo', 'dataset', 'objective'],
    'traintuple': ['traintuple'],
    'testtuple': ['testtuple'],
    'composite_traintuple': ['composite_traintuple']
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
    return {filter_key, object_type} <= {'algo', 'composite_algo'}


def filter_list(object_type, data, query_params):

    filters = get_filters(query_params)

    object_list = []

    for user_filter in filters:

        for filter_key, subfilters in user_filter.items():

            if filter_key not in AUTHORIZED_FILTERS[object_type]:
                raise Exception(f'Not authorized filter key {filter_key} for asset {object_type}')

            # Will be appended in object_list after been filtered
            filtered_list = data

            if _same_nature(filter_key, object_type):
                # Filter by own asset
                if filter_key == 'model':
                    for attribute, val in subfilters.items():
                        filtered_list = [x for x in filtered_list
                                         if x['traintuple']['outModel'] is not None and
                                         x['traintuple']['outModel']['hash'] in val]
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
                filtering_data = query_ledger(fcn=FILTER_QUERIES[filter_key], args=[])

                filtering_data = filtering_data if filtering_data else []

                if filter_key in ('algo', 'composite_algo'):
                    for attribute, val in subfilters.items():
                        filtering_data = [x for x in filtering_data if x[attribute] in val]
                        hashes = [x['key'] for x in filtering_data]

                        if object_type == 'model':
                            filtered_list = [x for x in filtered_list
                                             if x['traintuple']['algo']['hash'] in hashes]

                elif filter_key == 'model':
                    for attribute, val in subfilters.items():
                        filtering_data = [x for x in filtering_data
                                          if x['outModel'] is not None and x['outModel'][attribute] in val]

                        if object_type == 'algo':
                            hashes = [x['algo']['hash'] for x in filtering_data]
                            filtered_list = [x for x in filtered_list if x['key'] in hashes]

                        elif object_type == 'dataset':
                            hashes = [x['objective']['hash'] for x in filtering_data]
                            filtered_list = [x for x in filtered_list
                                             if x['objectiveKey'] in hashes]

                        elif object_type == 'objective':
                            hashes = [x['objective']['hash'] for x in filtering_data]
                            filtered_list = [x for x in filtered_list if x['key'] in hashes]

                elif filter_key == 'dataset':
                    for attribute, val in subfilters.items():
                        filtering_data = [x for x in filtering_data if x[attribute] in val]
                        hashes = [x['key'] for x in filtering_data]

                        if object_type == 'model':
                            filtered_list = [x for x in filtered_list
                                             if x['traintuple']['dataset']['openerHash'] in hashes]
                        elif object_type == 'objective':
                            objectiveKeys = [x['objectiveKey'] for x in filtering_data]
                            filtered_list = [x for x in filtered_list
                                             if x['key'] in objectiveKeys or
                                             (x['testDataset'] and x['testDataset']['dataManagerKey'] in hashes)]

                elif filter_key == 'objective':
                    for attribute, val in subfilters.items():
                        if attribute == 'metrics':  # specific to nested metrics
                            filtering_data = [x for x in filtering_data if x[attribute]['name'] in val]
                        else:
                            filtering_data = [x for x in filtering_data if x[attribute] in val]

                        hashes = [x['key'] for x in filtering_data]

                        if object_type == 'model':
                            filtered_list = [x for x in filtered_list
                                             if x['traintuple']['objective']['hash'] in hashes]
                        elif object_type == 'dataset':
                            filtered_list = [x for x in filtered_list
                                             if x['objectiveKey'] in hashes]

            object_list.append(filtered_list)

    return object_list
