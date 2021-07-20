from rest_framework import pagination
from rest_framework import status
from rest_framework.response import Response


class EndlessPagination(pagination.BasePagination):

    def __init__(self):
        self.has_next_page = False
        self.page_size = 20

    def paginate_queryset(self, queryset, request, view=None):
        # refresh most updated
        if 'created_at__gt' in request.query_params:
            created_at__gt = request.query_params['created_at__gt']
            num_new_tweets = queryset.filter(created_at__gt=created_at__gt).count()
            # new tweets not enough for one page
            if num_new_tweets >= self.page_size:
                queryset = queryset.filter(created_at__gt=created_at__gt)

        # scrolling down
        if 'created_at__lt' in request.query_params:
            created_at__lt = request.query_params['created_at__lt']
            queryset = queryset.filter(created_at__lt=created_at__lt)

        queryset = queryset[:self.page_size+1]
        self.has_next_page = len(queryset) > self.page_size
        return queryset[:self.page_size]

    def get_paginated_response(self, data):
        return Response({
            'has_next_page': self.has_next_page,
            'results': data,
        }, status=status.HTTP_200_OK)

    def to_html(self):
        pass
