from rest_framework import pagination
from rest_framework import status
from rest_framework.response import Response
from dateutil import parser
from django.conf import settings


class EndlessPagination(pagination.BasePagination):

    def __init__(self):
        self.has_next_page = False
        self.page_size = 20

    def _paginate_ordered_list(self, reversed_list, request):
        if 'created_at__gt' in request.query_params:
            created_at__gt = parser.isoparse(request.query_params['created_at__gt'])
            objects = []
            for index, obj in enumerate(reversed_list):
                if obj.created_at > created_at__gt:
                    objects.append(obj)
                else:
                    break
            self.has_next_page = False
            return objects

        index = 0
        if 'created_at__lt' in request.query_params:
            created_at__lt = parser.isoparse(request.query_params['created_at__lt'])
            for index, obj in enumerate(reversed_list):
                if obj.created_at < created_at__lt:
                    break
            else:
                reversed_list = []
        self.has_next_page = len(reversed_list) > index + self.page_size
        return reversed_list[index:(index+self.page_size)]

    def paginate_queryset(self, queryset, request, view=None):
        # refresh most updated
        if 'created_at__gt' in request.query_params:
            created_at__gt = request.query_params['created_at__gt']
            queryset = queryset.filter(created_at__gt=created_at__gt)
            self.has_next_page = False
            return queryset

        # scrolling down
        if 'created_at__lt' in request.query_params:
            created_at__lt = request.query_params['created_at__lt']
            queryset = queryset.filter(created_at__lt=created_at__lt)

        queryset = queryset[:self.page_size+1]
        self.has_next_page = len(queryset) > self.page_size
        return queryset[:self.page_size]

    def paginate_cached_list(self, cached_list, request, view=None):
        paginated_list = self._paginate_ordered_list(cached_list, request)
        # if paginate upward, return all fresh posts
        if 'created_at__gt' in request.query_params:
            return paginated_list
        # if there is next page, cache is still enough
        if self.has_next_page:
            return paginated_list
        # # of cached objects smaller than the cache limit, cache is enough
        if len(cached_list) < settings.REDIS_LIST_LENGTH_LIMIT:
            return paginated_list
        # cache not enough
        return None

    def get_paginated_response(self, data):
        return Response({
            'has_next_page': self.has_next_page,
            'results': data,
        }, status=status.HTTP_200_OK)

    def to_html(self):
        pass
