from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth import logout

from .models import CustomUser
from .serializers import EmailAuthTokenSerializer, UserSerializer


class EmailAuthTokenView(ObtainAuthToken):
    permission_classes = [AllowAny]
    serializer_class = EmailAuthTokenSerializer

    def post(self, request, *args, **kwargs):  # type: ignore[override]
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        user_data = UserSerializer(user, context={"request": request}).data
        return Response({"token": token.key, "user": user_data})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):  # type: ignore[override]
        token = getattr(request, "auth", None)
        if token:
            token.delete()
        else:
            Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response({"success": "Logout success"})


class UserViewSet(viewsets.ModelViewSet):
    permission_classes_by_action = {"create": [AllowAny]}
    queryset = CustomUser.objects.all().order_by("id")
    serializer_class = UserSerializer

    def get_permissions(self):  # type: ignore[override]
        try:
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            return [permission() for permission in self.permission_classes]


def signin(request):  # pragma: no cover - legacy alias
    view = EmailAuthTokenView.as_view()
    return view(request)


def signout(request, *args, **kwargs):  # pragma: no cover - legacy alias
    view = LogoutView.as_view()
    return view(request, *args, **kwargs)
