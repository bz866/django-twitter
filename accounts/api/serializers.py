from accounts.models import UserProfile
from django.contrib.auth.models import User
from rest_framework import exceptions, status
from rest_framework import serializers
from rest_framework.fields import CharField
from rest_framework.fields import EmailField
from rest_framework.fields import FileField
from rest_framework.serializers import SerializerMethodField


class UserSerializer(serializers.ModelSerializer):
    username = CharField(min_length=6, max_length=20)
    email = EmailField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email',)


class UserSerializerWithProfile(serializers.ModelSerializer):
    nickname = CharField(source='profile.nickname')
    avatar_url = SerializerMethodField()

    def get_avatar_url(self, obj):
        if obj.profile.avatar:
            return obj.profile.avatar.url
        return None

    class Meta:
        model = User
        fields = ('id', 'username', 'nickname', 'avatar_url')


class UserProfileSerializerForUpdate(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('nickname', 'avatar')


class UserSerializerForTweet(UserSerializerWithProfile):
    pass


class UserSerializerForFriendship(UserSerializerWithProfile):
    pass


class UserSerializerForComment(UserSerializerWithProfile):
    pass


class UserSerializerForLike(UserSerializerWithProfile):
    pass


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
            raise exceptions.ValidationError({
                "username": [
                    "This username has been occupied."
                ],
            })
        # email occupied
        elif User.objects.filter(email=attrs['email']).exists():
            raise exceptions.ValidationError({
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

    def validate(self, attrs):
        attrs['username'] = attrs['username'].lower()
        if not User.objects.filter(username=attrs['username']).exists():
            raise exceptions.ValidationError({
                "username": [
                    "User name not exist"
                ],
            })
        return attrs