from tweets.models import Tweet
from tweets.api.serializers import TweetSerializer
from tweets.api.serializers import TweetCreateSerializer
from tweets.api.serializers import TweetSerializerForDetail
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from newsfeeds.services import NewsFeedService
from utils.decorators import require_params


class TweetViewSet(viewsets.GenericViewSet):
    serializer_class = TweetCreateSerializer
    queryset = Tweet.objects.all()

    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny(),]
        return [IsAuthenticated(),]

    @require_params(require_attrs='query_params', params=['user_id'])
    def list(self, request):
        # select out all tweets of a specific user
        queryset = Tweet.objects.filter(
            user_id=request.query_params['user_id']
        ).order_by('-created_at')
        serializer = TweetSerializer(
            queryset,
            context={'request': request},
            many=True,
        )
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
        NewsFeedService().fanout_to_followers(tweet)
        serializer = TweetSerializer(
            instance=tweet,
            context={'request': request},
        )
        return Response({
            'success': True,
            'tweet': serializer.data,
        }, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        tweet = self.get_object()
        serializer = TweetSerializerForDetail(
            instance=tweet,
            context={'request': request},
        )
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )