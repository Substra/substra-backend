from rest_framework import serializers


class LedgerLearnupletSerializer(serializers.Serializer):
    model = serializers.CharField(min_length=69, max_length=69)
    train_data = serializers.ListField(child=serializers.CharField(min_length=69, max_length=69),
                                       min_length=1,
                                       max_length=None)

    def create(self, validated_data):
        problem = self.initial_data.get('problem')

        # TODO use asynchrone task for calling ledger

        # pass instance to validated True if ok, else create cron that delete instance.validated = False older than x days
