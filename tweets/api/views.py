from django.shortcuts import render
from tweets.models import Tweet
from tweets.api.serializers import (
    TweetSerializer,
    TweetCreateSerializer,
)
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)


# Create your views here.
class TweetViewSet(viewsets.GenericViewSet):
    serializer_class = TweetCreateSerializer
    queryset = Tweet.objects.all()

    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny(),]
        return [IsAuthenticated(),]

    def list(self, request):
        # check if user id in request parameter
        if 'user_id' not in request.query_params:
            return Response('missing user_id parameter', status=status.HTTP_400_BAD_REQUEST)

        # select out all tweets of a specific user
        queryset = Tweet.objects.filter(
            user_id=request.query_params['user_id']
        ).order_by('-created_at')
        serializer = TweetSerializer(queryset, many=True)

        # wrap the list of tweet contents in dict
        return Response({'tweet': serializer.data})

    def create(self, request):
        serializer = TweetCreateSerializer(
            data = request.data,
            context = {'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': "Please check the input",
                'error': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        tweet = serializer.save()
        return Response({
            'success': True,
            'tweet': TweetSerializer(tweet).data,
        }, status=status.HTTP_201_CREATED)
