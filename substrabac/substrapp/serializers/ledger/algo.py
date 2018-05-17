from rest_framework import serializers


class LedgerAlgoSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=1, max_length=60)
    permissions = serializers.CharField(min_length=1, max_length=60)

    def create(self, validated_data):
        instance_pkhash = self.initial_data.get('instance_pkhash')
        problem = self.initial_data.get('problem')

        # TODO use asynchrone task for calling ledger

        # pass instance to validated True if ok, else create cron that delete instance.validated = False older than x days
