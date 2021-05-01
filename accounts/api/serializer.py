from django.contrib.auth.models import User
from rest_framework import exceptions, status
from rest_framework import serializers
from rest_framework.fields import CharField, EmailField


class UserSerializer(serializers.Serializer):
    username = CharField(min_length=6, max_length=20)
    email = EmailField()

    class Meta:
        model = User
        field = ('id', 'username', 'email')

class SignUpSerializer(serializers.ModelSerializer):
    username = CharField(min_length=6, max_length=20)
    password = CharField(min_length=6, max_length=20)
    email = EmailField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def validate(self, attrs):
        attrs['username'] = attrs['username'].lower()
        attrs['email'] = attrs['email'].lower()
        # username occupied
        if User.objects.filter(username=attrs['username']).exists():
            return exceptions.ValidationError({
                "username": [
                    "This username has been occupied."
                ],
            })
        # email occupied
        if User.objects.filter(email=attrs['email']).exists():
            return exceptions.ValidationError({
                "email": [
                    "This email has been occupied."
                ],
            })
        return attrs

    def create(self, validated_attrs):
        username = validated_attrs['username']
        email = validated_attrs['email']
        password = validated_attrs['password']

        # create new user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email
        )
        return user

class LoginSerializer(serializers.Serializer):
    username = CharField()
    password = CharField()

    def validated(self, attrs):
        attrs['username'] = attrs['username'].lower()
        attrs['email'] = attrs['email'].lower()
        if not User.objects.filter(attrs['username']).exists():
            return exceptions.ValidationError({
                "username": [
                    "User name not exist"
                ],
            })
        return attrs