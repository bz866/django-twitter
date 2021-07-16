from accounts.api.serializers import LoginSerializer
from accounts.api.serializers import SignUpSerializer
from accounts.api.serializers import UserSerializer
from django.contrib.auth import authenticate as django_authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from accounts.models import UserProfile
from rest_framework.permissions import IsAuthenticated
from accounts.api.serializers import UserProfileSerializerForUpdate
from utils.permissions import IsObjectOwner


class UserViewSet(viewsets.ViewSet):
    serializer_class = UserSerializer
    permission_classes = [AllowAny,]
    queryset = User.objects.all()


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = SignUpSerializer
    permission_classes = [AllowAny,]

    @action(methods=['POST'], detail=False)
    def signup(self, request):
        serializer = SignUpSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Please check input",
                "error": serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        # valid input, create user
        user = serializer.save()
        django_login(request, user)
        return Response({
            "success": True,
            "user": UserSerializer(instance=user).data
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "error": serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        # login
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = django_authenticate(request, username=username, password=password)

        # username and password not match
        if not user or user.is_anonymous:
            return Response({
                "success": False,
                "message": "Username and password not match"
            }, status=status.HTTP_400_BAD_REQUEST)

        # valid username and password
        django_login(request, user)
        return Response({
            "success": True,
            "user": UserSerializer(instance=user).data,
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    def logout(self, request):
        if request.user.is_authenticated:
            django_logout(request)
        return Response({
            "success": True,
        }, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False)
    def login_status(self, request):
        user = request.user
        if not user or user.is_anonymous:
            return Response({
                'has_logged_in': False,
            }, status=status.HTTP_200_OK)

        elif user.is_authenticated:
            return Response({
                'has_logged_in': True,
                'user': UserSerializer(instance=user).data,
            })

        else:
            return Response({
                'has_loggin_in': False,
            }, status=status.HTTP_200_OK)


class UserProfileViewSet(
    viewsets.GenericViewSet,
    UpdateModelMixin,
):
    queryset = UserProfile.objects.all()
    permission_classes = [IsAuthenticated, IsObjectOwner,]
    serializer_class = UserProfileSerializerForUpdate


