from django.shortcuts import render
from tweets.models import Tweet
from tweets.api.serializers import TweetSerializer
from rest_framework.viewsets import (
    GenericViewSet,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)


# Create your views here.
class TweetViewSet(GenericViewSet):
    serializer_class = TweetSerializer
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

    # def retrieve(self, request, pk):
    #     queryset = Tweet.objects.all()
    #     tweet = get_object_or_404(queryset, pk=pk)
    #     serializer = TweetSerializer(tweet)
    #     return Response(serializer.data)
