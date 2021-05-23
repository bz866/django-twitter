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
        if 'user_id' not in request.query_params:
            return Response(
                "Please check input. 'user_id' is required.",
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = NewsFeed.objects.filter(user_id=request.query_params['user_id'])
        serializer = NewsFeedSerializer(queryset)
        return Response({'newsfeed': serializer.data})