from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from newsfeeds.models import NewsFeed
from newsfeeds.api.serializers import NewsFeedSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny


class NewsFeedViewSet(viewsets.GenericViewSet):

    def get_permissions(self):
        if self.action == 'list':
            return [IsAuthenticated(), ]
        return [AllowAny(), ]

    def list(self, request):
        queryset = NewsFeed.objects.filter(user_id=request.user.id)
        serializer = NewsFeedSerializer(
            queryset,
            context={'request': request},
            many=True,
        )
        return Response({'newsfeed': serializer.data})