import os
import tempfile

import requests
from django.http import Http404
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from substrapp.models import Model
from substrapp.serializers import ModelSerializer

# from hfc.fabric import Client
# cli = Client(net_profile="../network.json")
from substrapp.utils import queryLedger
from substrapp.views.utils import get_filters, ComputeHashMixin, getObjectFromLedger, CustomFileResponse, JsonException


class ModelViewSet(mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   ComputeHashMixin,
                   GenericViewSet):
    queryset = Model.objects.all()
    serializer_class = ModelSerializer

    # permission_classes = (permissions.IsAuthenticated,)

    def create_or_update_model(self, model, pk):
        try:
            # get challenge description from remote node
            url = model['endModel']['storageAddress']
            try:
                r = requests.get(url, headers={'Accept': 'application/json;version=0.0'})  # TODO pass cert
            except:
                raise Exception(f'Failed to fetch {url}')
            else:
                if r.status_code != 200:
                    raise Exception(f'end to end node report {r.text}')

                try:
                    computed_hash = self.compute_hash(r.content)
                except Exception:
                    raise Exception('Failed to fetch endModel file')
                else:
                    if computed_hash != pk:
                        msg = 'computed hash is not the same as the hosted file. Please investigate for default of synchronization, corruption, or hacked'
                        raise Exception(msg)

                    f = tempfile.TemporaryFile()
                    f.write(r.content)

                    # save/update challenge in local db for later use
                    instance, created = Model.objects.update_or_create(pkhash=pk, validated=True)
                    instance.file.save('model', f)
        except Exception as e:
            raise e
        else:
            return instance

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        if len(pk) != 64:
            return Response({'message': f'Wrong pk {pk}'}, status.HTTP_400_BAD_REQUEST)

        try:
            int(pk, 16)  # test if pk is correct (hexadecimal)
        except:
            return Response({'message': f'Wrong pk {pk}'}, status.HTTP_400_BAD_REQUEST)
        else:
            # get instance from remote node
            try:
                data = getObjectFromLedger(pk)
            except JsonException as e:
                return Response(e.msg, status=status.HTTP_400_BAD_REQUEST)
            else:
                error = None
                instance = None
                try:
                    # try to get it from local db to check if description exists
                    instance = self.get_object()
                except Http404:
                    if data['endModel'] is None:
                        error = f'This traintuple key {pk} does not have a related endModel'
                    else:
                        try:
                            instance = self.create_or_update_model(data, pk)
                        except Exception as e:
                            error = e
                else:
                    # check if instance has file
                    if not instance.file:
                        try:
                            instance = self.create_or_update_model(data, pk)
                        except Exception as e:
                            error = e
                finally:
                    if error is not None:
                        return Response({'message': str(error)}, status=status.HTTP_400_BAD_REQUEST)

                    # do not give access to local files address
                    if instance is not None:
                        serializer = self.get_serializer(instance, fields=('owner', 'pkhash', 'creation_date', 'last_modified'))
                        data.update(serializer.data)
                    else:
                        data = {'message': 'Fail to get instance'}

                    return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        # can modify result by interrogating `request.version`

        data, st = queryLedger({
            'args': '{"Args":["queryTraintuples"]}'
        })
        algoData = None
        challengeData = None
        datasetData = None

        # init list to return
        if data is None:
            data = []
        l = [data]

        if st == 200:
            # parse filters
            query_params = request.query_params.get('search', None)

            if query_params is not None:
                try:
                    filters = get_filters(query_params)
                except Exception as exc:
                    return Response(
                        {'message': f'Malformed search filters {query_params}'},
                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    # filtering, reinit l to empty array
                    l = []
                    for idx, filter in enumerate(filters):
                        # init each list iteration to data
                        if data is None:
                            data = []
                        l.append(data)
                        for k, subfilters in filter.items():
                            if k == 'model':  # filter by own key
                                for key, val in subfilters.items():
                                    l[idx] = [x for x in l[idx] if x['endModel'] is not None and x['endModel']['hash'] in val]
                            elif k == 'algo':  # select model used by these algo
                                if not algoData:
                                    # TODO find a way to put this call in cache
                                    algoData, st = queryLedger({
                                        'args': '{"Args":["queryAlgos"]}'
                                    })
                                    if st != 200:
                                        return Response(algoData, status=st)

                                    if algoData is None:
                                        algoData = []
                                for key, val in subfilters.items():
                                    filteredData = [x for x in algoData if x[key] in val]
                                    algoHashes = [x['key'] for x in filteredData]
                                    l[idx] = [x for x in l[idx] if x['algo']['hash'] in algoHashes]
                            elif k == 'dataset':  # select model which trainData.openerHash is
                                if not datasetData:
                                    # TODO find a way to put this call in cache
                                    datasetData, st = queryLedger({
                                        'args': '{"Args":["queryDatasets"]}'
                                    })
                                    if st != 200:
                                        return Response(datasetData, status=st)

                                    if datasetData is None:
                                        datasetData = []
                                for key, val in subfilters.items():
                                    filteredData = [x for x in datasetData if x[key] in val]
                                    datasetHashes = [x['key'] for x in filteredData]
                                    l[idx] = [x for x in l[idx] if x['trainData']['openerHash'] in datasetHashes]
                            elif k == 'challenge':  # select challenge used by these datasets
                                if not challengeData:
                                    # TODO find a way to put this call in cache
                                    challengeData, st = queryLedger({
                                        'args': '{"Args":["queryChallenges"]}'
                                    })
                                    if st != 200:
                                        return Response(challengeData, status=st)

                                    if challengeData is None:
                                        challengeData = []
                                for key, val in subfilters.items():
                                    if key == 'metrics':  # specific to nested metrics
                                        filteredData = [x for x in challengeData if x[key]['name'] in val]
                                    else:
                                        filteredData = [x for x in challengeData if x[key] in val]
                                    challengeKeys = [x['key'] for x in filteredData]
                                    l[idx] = [x for x in l[idx] if x['challenge']['hash'] in challengeKeys]

        return Response(l, status=st)

    @action(detail=True)
    def file(self, request, *args, **kwargs):
        object = self.get_object()

        # TODO query model permissions

        data = getattr(object, 'file')
        return CustomFileResponse(open(data.path, 'rb'), as_attachment=True, filename=os.path.basename(data.path))
