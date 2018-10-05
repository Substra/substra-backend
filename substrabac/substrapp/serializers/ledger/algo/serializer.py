from rest_framework import serializers

from .tasks import createLedgerAlgo
from substrapp.models.utils import compute_hash


class LedgerAlgoSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1, max_length=60)
    challenge_key = serializers.CharField(min_length=1, max_length=256)
    permissions = serializers.CharField(min_length=1, max_length=60)

    def create(self, validated_data):
        instance = self.initial_data.get('instance')
        name = validated_data.get('name')
        permissions = validated_data.get('permissions')
        challenge_key = validated_data.get('challenge_key')

        # TODO, create a datamigration with new Site domain name when we will know the name of the final website
        # current_site = Site.objects.get_current()
        request = self.context.get('request', None)
        protocol = 'https://' if request.is_secure() else 'http://'
        host = '' if request is None else request.get_host()

        args = '"%(name)s", "%(algoHash)s", "%(storageAddress)s", "%(descriptionHash)s", "%(descriptionStorageAddress)s", "%(associatedChallenge)s", "%(permissions)s"' % {
            'name': name,
            'algoHash': compute_hash(instance.file),
            'storageAddress': protocol + host + instance.file.url,
            'descriptionHash': compute_hash(instance.description),
            'descriptionStorageAddress': protocol + host + instance.description.url,
            'associatedChallenge': challenge_key,
            'permissions': permissions
        }

        # use a celery task, as we are in an http request transaction
        createLedgerAlgo.delay(args, instance.pkhash)

        return {
            'message': 'Algo added in local db waiting for validation. The susbtra network has been notified for adding this Algo'}
