import tempfile

import requests
from django.conf import settings
from django.db import IntegrityError
from django.http import Http404
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

# from hfc.fabric import Client
# cli = Client(net_profile="../network.json")
from substrapp.models import Dataset
from substrapp.serializers import DatasetSerializer, LedgerDatasetSerializer
from substrapp.utils import queryLedger
from substrapp.views.utils import get_filters, getObjectFromLedger, ManageFileMixin, ComputeHashMixin


class DatasetViewSet(mixins.CreateModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.ListModelMixin,
                     ComputeHashMixin,
                     ManageFileMixin,
                     GenericViewSet):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer

    def perform_create(self, serializer):
        return serializer.save()

    def create(self, request, *args, **kwargs):
        data = request.data

        serializer = self.get_serializer(data={
            'data_opener': data.get('data_opener'),
            'description': data.get('description'),
            'name': data.get('name'),
        })

        serializer.is_valid(raise_exception=True)

        # create on db
        try:
            instance = self.perform_create(serializer)
        except IntegrityError as exc:
            return Response({'message': 'A dataset with this opener file already exists.'},
                            status=status.HTTP_409_CONFLICT)
        else:
            # init ledger serializer
            ledger_serializer = LedgerDatasetSerializer(data={'name': data.get('name'),
                                                              'permissions': data.get('permissions'),
                                                              'type': data.get('type'),
                                                              'challenge_keys': data.getlist('challenge_keys'),
                                                              'instance': instance},
                                                        context={'request': request})

            if not ledger_serializer.is_valid():
                # delete instance
                instance.delete()
                raise ValidationError(ledger_serializer.errors)

            # create on ledger
            data = ledger_serializer.create(ledger_serializer.validated_data)

            st = status.HTTP_201_CREATED
            headers = self.get_success_headers(serializer.data)

            data.update(serializer.data)
            return Response(data, status=st, headers=headers)

    # TODO refacto
    def create_or_update_dataset(self, instance, dataset, pk):

        # create instance if does not exist
        if not instance:
            instance, created = Dataset.objects.update_or_create(pkhash=pk, name=dataset['name'], validated=True)

        if not instance.data_opener:
            try:
                url = dataset['openerStorageAddress']
                try:
                    r = requests.get(url, headers={'Accept': 'application/json;version=0.0'})  # TODO pass cert
                except:
                    raise 'Failed to fetch %s' % url
                else:
                    if r.status_code != 200:
                        raise Exception('end to end node report %s' % r.text)

                    try:
                        computed_hash = self.compute_hash(r.content)
                    except Exception:
                        raise Exception('Failed to fetch opener file')
                    else:
                        if computed_hash != pk:
                            msg = 'computed hash is not the same as the hosted file. Please investigate for default of synchronization, corruption, or hacked'
                            raise Exception(msg)

                        f = tempfile.TemporaryFile()
                        f.write(r.content)

                        # save/update data_opener in local db for later use
                        instance.data_opener.save('opener.py', f)

            except Exception as e:
                raise e

        if not instance.description:
            # do the same for description
            url = dataset['description']['storageAddress']
            try:
                r = requests.get(url, headers={'Accept': 'application/json;version=0.0'})  # TODO pass cert
            except:
                raise 'Failed to fetch %s' % url
            else:
                if r.status_code != 200:
                    raise Exception('end to end node report %s' % r.text)

                try:
                    computed_hash = self.compute_hash(r.content)
                except Exception:
                    raise Exception('Failed to fetch description file')
                else:
                    if computed_hash != dataset['description']['hash']:
                        msg = 'computed hash is not the same as the hosted file. Please investigate for default of synchronization, corruption, or hacked'
                        raise Exception(msg)

                    f = tempfile.TemporaryFile()
                    f.write(r.content)

                    # save/update description in local db for later use
                    instance.description.save('description.md', f)

        return instance

    def retrieve(self, request, *args, **kwargs):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs[lookup_url_kwarg]

        if len(pk) != 64:
            return Response({'message': 'Wrong pk %s' % pk}, status.HTTP_400_BAD_REQUEST)

        try:
            int(pk, 16)  # test if pk is correct (hexadecimal)
        except:
            return Response({'message': 'Wrong pk %s' % pk}, status.HTTP_400_BAD_REQUEST)
        else:
            # get instance from remote node
            try:
                data = getObjectFromLedger(pk)
            except Exception as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
            else:
                error = None
                instance = None
                try:
                    # try to get it from local db to check if description exists
                    instance = self.get_object()
                except Http404:
                    try:
                        instance = self.create_or_update_dataset(instance, data, pk)
                    except Exception as e:
                        error = e
                else:
                    # check if instance has description
                    if not instance.description or not instance.data_opener:
                        try:
                            instance = self.create_or_update_dataset(instance, data, pk)
                        except Exception as e:
                            error = e
                finally:
                    if error is not None:
                        return Response(error, status=status.HTTP_400_BAD_REQUEST)

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
            'org': settings.LEDGER['org'],
            'peer': settings.LEDGER['peer'],
            'args': '{"Args":["queryDatasets"]}'
        })
        challengeData = None
        algoData = None
        modelData = None

        # parse filters
        query_params = request.query_params.get('search', None)
        l = [data]
        if query_params is not None:
            try:
                filters = get_filters(query_params)
            except Exception as exc:
                return Response(
                    {'message': 'Malformed search filters %(query_params)s' % {'query_params': query_params}},
                    status=status.HTTP_400_BAD_REQUEST)
            else:
                # filtering, reinit l to empty array
                l = []
                for idx, filter in enumerate(filters):
                    # init each list iteration to data
                    l.append(data)
                    for k, subfilters in filter.items():
                        if k == 'dataset':  # filter by own key
                            for key, val in subfilters.items():
                                l[idx] = [x for x in l[idx] if x[key] in val]
                        elif k == 'challenge':  # select challenge used by these datasets
                            if not challengeData:
                                # TODO find a way to put this call in cache
                                challengeData, st = queryLedger({
                                    'org': settings.LEDGER['org'],
                                    'peer': settings.LEDGER['peer'],
                                    'args': '{"Args":["queryChallenges"]}'
                                })
                                if st != 200:
                                    return Response(challengeData, status=st)

                            for key, val in subfilters.items():
                                if key == 'metrics':  # specific to nested metrics
                                    filteredData = [x for x in challengeData if x[key]['name'] in val]
                                else:
                                    filteredData = [x for x in challengeData if x[key] in val]
                                challengeKeys = [x['key'] for x in filteredData]
                                l[idx] = [x for x in l[idx] if [x for x in x['challengeKeys'] if x in challengeKeys]]
                        elif k == 'algo':  # select challenge used by these algo
                            if not algoData:
                                # TODO find a way to put this call in cache
                                algoData, st = queryLedger({
                                    'org': settings.LEDGER['org'],
                                    'peer': settings.LEDGER['peer'],
                                    'args': '{"Args":["queryAlgos"]}'
                                })
                                if st != 200:
                                    return Response(algoData, status=st)

                            for key, val in subfilters.items():
                                filteredData = [x for x in algoData if x[key] in val]
                                challengeKeys = [x['challengeKey'] for x in filteredData]
                                l[idx] = [x for x in l[idx] if [x for x in x['challengeKeys'] if x in challengeKeys]]
                        elif k == 'model':  # select challenges used by endModel hash
                            if not modelData:
                                # TODO find a way to put this call in cache
                                modelData, st = queryLedger({
                                    'org': settings.LEDGER['org'],
                                    'peer': settings.LEDGER['peer'],
                                    'args': '{"Args":["queryTraintuples"]}'
                                })
                                if st != 200:
                                    return Response(modelData, status=st)

                            for key, val in subfilters.items():
                                filteredData = [x for x in modelData if x['endModel'][key] in val]
                                challengeKeys = [x['challenge']['hash'] for x in filteredData]
                                l[idx] = [x for x in l[idx] if [x for x in x['challengeKeys'] if x in challengeKeys]]

        return Response(l, status=st)

    @action(detail=True)
    def description(self, request, *args, **kwargs):
        return self.manage_file('description')

    @action(detail=True)
    def opener(self, request, *args, **kwargs):
        return self.manage_file('data_opener')

