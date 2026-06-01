from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from entailment.dto import EntailmentRequest
from entailment.services import entailment_service

from judge.serializers import (
    ErrorResponseSerializer,
    JudgeResultSerializer,
    JudgeRequestSerializer,
)

from drf_spectacular.utils import extend_schema


class JudgeViewSet(viewsets.ViewSet):
    @extend_schema(
        summary="Judge entailment",
        request=JudgeRequestSerializer,
        responses={
            200: JudgeResultSerializer,
            400: ErrorResponseSerializer,
            429: ErrorResponseSerializer,
        },
    )
    def create(self, request):
        serializer = JudgeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data: JudgeRequestSerializer = serializer.validated_data

        result = entailment_service.run_inference(
            [EntailmentRequest(premise=data["sentence1"], hypothesis=data["sentence2"])]
        )

        result_serializer = JudgeResultSerializer(result[0])
        return Response(result_serializer.data)

    @extend_schema(
        summary="Judge entailment bulk",
        request=JudgeRequestSerializer(many=True),
        responses={
            200: JudgeResultSerializer(many=True),
            400: ErrorResponseSerializer,
            429: ErrorResponseSerializer,
        },
    )
    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk(self, request):
        serializer = JudgeRequestSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        requests = [
            EntailmentRequest(
                premise=item["sentence1"],
                hypothesis=item["sentence2"],
            )
            for item in serializer.validated_data
        ]

        result = entailment_service.run_inference(requests)

        result_serializer = JudgeResultSerializer(result, many=True)
        return Response(result_serializer.data)
