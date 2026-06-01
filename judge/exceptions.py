from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.exceptions import Throttled


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, serializers.ValidationError):
        return Response(
            {
                "message": "Validation error",
                "details": exc.detail,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    elif isinstance(exc, Throttled):
        return Response(
            {
                "message": "Rate Limit Error",
                "details": exc.detail,
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    return response
