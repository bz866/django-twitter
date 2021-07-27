from django.db.models.signals import post_save
from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.listeners import push_newsfeed_to_cache
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
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
        cached_newsfeeds = NewsFeedService.load_newsfeeds_through_cache(
            user_id=request.user.id
        )
        page = self.paginator.paginate_cached_list(cached_newsfeeds, request)
        # cache not enough, access the db directly for extra
        if not page:
            newsfeeds = NewsFeed.objects.filter(user_id=request.user.id)
            page = self.paginate_queryset(newsfeeds)
        serializer = NewsFeedSerializer(
            page,
            context={'request': request},
            many=True,
        )
        return self.get_paginated_response(serializer.data)


# clear Redis cache in create()
post_save.connect(push_newsfeed_to_cache, sender=NewsFeed)
