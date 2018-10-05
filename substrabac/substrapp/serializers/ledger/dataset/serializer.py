from rest_framework import serializers

from .tasks import createLedgerDataset

from substrapp.models.utils import compute_hash


class LedgerDatasetSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=256)
    type = serializers.CharField(max_length=256)
    challenge_keys = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64, allow_blank=True),
                                           max_length=None)
    permissions = serializers.CharField(min_length=1, max_length=60)

    def create(self, validated_data):
        instance = self.initial_data.get('instance')
        name = validated_data.get('name')
        type = validated_data.get('type')
        permissions = validated_data.get('permissions')
        challenge_keys = validated_data.get('challenge_keys')

        # TODO, create a datamigration with new Site domain name when we will know the name of the final website
        # current_site = Site.objects.get_current()
        request = self.context.get('request', None)
        protocol = 'https://' if request.is_secure() else 'http://'
        host = '' if request is None else request.get_host()

        args = '"%(name)s", "%(openerHash)s", "%(openerStorageAddress)s", "%(type)s", "%(descriptionHash)s", "%(descriptionStorageAddress)s", "%(challengeKeys)s", "%(permissions)s"' % {
            'name': name,
            'openerHash': compute_hash(instance.data_opener),
            'openerStorageAddress': protocol + host + instance.data_opener.url,
            'type': type,
            'descriptionHash': compute_hash(instance.description),
            'descriptionStorageAddress': protocol + host + instance.description.url,
            'challengeKeys': ','.join([x for x in challenge_keys]),
            'permissions': permissions
        }

        # use a celery task, as we are in an http request transaction
        createLedgerDataset.delay(args, instance.pkhash)

        return {
            'message': 'Dataset added in local db waiting for validation. The susbtra network has been notified for adding this Dataset'}
