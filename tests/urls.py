from django.http import Http404
from django.urls import path
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_envelope.handler import ApiError


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=10)


class SignupView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"ok": True}, status=201)


class PayView(APIView):
    def post(self, request):
        raise ApiError(
            "The account does not hold enough funds for this payment.",
            code="insufficient_funds",
            details={"available": "10.00", "requested": "50.00"},
            status_code=422,
        )


class BoomView(APIView):
    def post(self, request):
        raise RuntimeError("kaboom")


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"user": "you"})


@api_view(["GET"])
@permission_classes([AllowAny])
def missing(request):
    raise Http404


urlpatterns = [
    path("signup/", SignupView.as_view()),
    path("pay/", PayView.as_view()),
    path("boom/", BoomView.as_view()),
    path("me/", MeView.as_view()),
    path("missing/", missing),
]
