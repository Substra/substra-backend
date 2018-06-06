from rest_framework import serializers


class LedgerProblemSerializer(serializers.Serializer):
    test_data = serializers.ListField(child=serializers.CharField(min_length=64, max_length=64),
                                      min_length=1,
                                      max_length=None)
    name = serializers.CharField(min_length=1, max_length=60)

    def create(self, validated_data):
        instance_pkhash = self.initial_data.get('instance_pkhash')

        # TODO use asynchrone task for calling ledger

        # pass instance to validated True if ok, else create cron that delete instance.validated = False older than x days
