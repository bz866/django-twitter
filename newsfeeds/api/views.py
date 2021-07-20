from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.models import NewsFeed
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from utils.paginations import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    pagination_class = EndlessPagination

    def get_permissions(self):
        if self.action == 'list':
            return [IsAuthenticated(), ]
        return [AllowAny(), ]

    def list(self, request):
        queryset = NewsFeed.objects.filter(user_id=request.user.id)
        page = self.paginate_queryset(queryset)
        serializer = NewsFeedSerializer(
            page,
            context={'request': request},
            many=True,
        )
        return self.get_paginated_response(serializer.data)