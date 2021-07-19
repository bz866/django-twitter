from rest_framework import pagination
from rest_framework.response import Response
from rest_framework import status


class FriendShipPagination(pagination.PageNumberPagination):
    page_size = 10 # default page size
    page_size_query_param = 'size' # query_param to define the page size
    max_page_size = 20 # max page size in query_param
    page_query_param = 'page' # query_param navigate to a certain page

    def get_paginated_response(self, data):
        """
        Override the response from the pagination
        """
        return Response({
            'total_results': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'page_number': self.page.number,
            'has_next_page': self.page.has_next(),
            'friendships': data,
        }, status=status.HTTP_200_OK)