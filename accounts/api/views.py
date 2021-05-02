from django.contrib.auth.models import User
from django.contrib.auth import (
    login as django_login,
    logout as django_logout,
    authenticate as django_authenticate
)
from rest_framework import exceptions, status
from rest_framework import viewsets
from accounts.api.serializer import UserSerializer, SignUpSerializer, LoginSerializer
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action

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
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=False)
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        # login
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = django_login(username, password)

        # username and password not match
        if not user or user.is_anonymous:
            return Response({
                "success": False,
                "message": "Username and password not match"
            }, status=status.HTTP_400_BAD_REQUEST)

        # successfully login
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

        elif user.is_autheticated:
            return Response({
                'has_logged_in': True,
                'user': UserSerializer(instance=user).data,
            })

        else:
            return Response({
                'has_loggin_in': False,
            }, status=status.HTTP_200_OK)
