from rest_framework import serializers
from entailment.enum import EntailmentLabel
from django.conf import settings

ENTAILMENT_LABEL_CHOICES = [(label.value, label.value) for label in EntailmentLabel]


class BulkJudgeRequestListSerializer(serializers.ListSerializer):
    def validate(self, data):
        if len(data) > settings.BULK_JUDGE_LIMIT:
            raise serializers.ValidationError(
                f"Bulk requests may include at most {settings.BULK_JUDGE_LIMIT} items."
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


class ErrorResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    details = serializers.DictField(required=False)
