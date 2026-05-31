from rest_framework import serializers
from entailment.enum import EntailmentLabel

ENTAILMENT_LABEL_CHOICES = [(label.value, label.value) for label in EntailmentLabel]


class BulkJudgeRequestListSerializer(serializers.ListSerializer):
    def validate(self, data):
        if len(data) > 100:
            raise serializers.ValidationError(
                "Bulk requests may include at most 100 items."
            )
        return data


class JudgeRequestSerializer(serializers.Serializer):
    sentence1 = serializers.CharField()
    sentence2 = serializers.CharField()

    class Meta:
        list_serializer_class = BulkJudgeRequestListSerializer


class JudgeResultSerializer(serializers.Serializer):
    label = serializers.ChoiceField(choices=ENTAILMENT_LABEL_CHOICES)
    score = serializers.FloatField()
