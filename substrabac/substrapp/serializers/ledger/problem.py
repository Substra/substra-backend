from rest_framework import serializers


class LedgerProblemSerializer(serializers.Serializer):
    test_data = serializers.ListField(child=serializers.CharField(min_length=69, max_length=69),
                                      min_length=1,
                                      max_length=None)
    name = serializers.CharField(min_length=1, max_length=60)

    def create(self, validated_data):
        problem_pkhash = self.initial_data.get('problem_pkhash')

        # run smart contract to register problem in ledger
        # TODO using problem.pk as description hash
        # need to compute metrics hash
        # metrics_hash = compute_hash(problem.metrics)
        # print(metrics_hash)

        return {}