from rest_framework import pagination
from rest_framework import status
from rest_framework.response import Response
from dateutil import parser


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
            self.has_next_page = len(objects) > self.page_size
            return objects[:self.page_size]

        elif 'created_at__lt' in request.query_params:
            index = 0
            created_at__lt = parser.isoparse(request.query_params['created_at__lt'])
            for index, obj in enumerate(reversed_list):
                if obj.created_at < created_at__lt:
                    break
            else:
                reversed_list = []
            self.has_next_page = len(reversed_list) > index + self.page_size
            return reversed_list[index:(index+self.page_size)]

        # no timestamp filter
        else:
            self.has_next_page = len(reversed_list) > self.page_size
            return reversed_list[:self.page_size]

    def paginate_queryset(self, queryset, request, view=None):
        if type(queryset) == list:
            return self._paginate_ordered_list(queryset, request)

        # refresh most updated
        if 'created_at__gt' in request.query_params:
            created_at__gt = request.query_params['created_at__gt']
            num_new = queryset.filter(created_at__gt=created_at__gt).count()
            if num_new >= self.page_size:
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
