from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from friendships.api.paginations import FriendShipPagination
from friendships.api.serializers import FriendshipCreateSerializer
from friendships.api.serializers import FriendshipFollowerSerializer
from friendships.api.serializers import FriendshipFollowingSerializer
from friendships.models import Friendship
from friendships.services import FriendshipService
from ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from utils.decorators import require_params
from utils.paginations import EndlessPagination
from friendships.hbase_models import HBaseFollower, HBaseFollowing
from gatekeeper.models import GateKeeper


class FriendshipViewSet(viewsets.GenericViewSet):
    serializer_class = FriendshipCreateSerializer
    queryset = User.objects.all()
    pagination_class = EndlessPagination

    def get_permissions(self):
        if self.action == 'list':
            return [IsAuthenticated(),]
        return [IsAuthenticated(),]

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    @method_decorator(ratelimit(key='user', rate='3/s', method='GET', block=True))
    def followers(self, request, pk):
        paginator = self.paginator
        # select out followers for a specific user
        if GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            page = paginator.paginate_hbase(HBaseFollower, (pk, ), request)
        else:
            friendships = Friendship.objects.filter(to_user_id=pk)
            page = paginator.paginate_queryset(friendships)
        serializer = FriendshipFollowerSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    @method_decorator(ratelimit(key='user', rate='3/s', method='GET', block=True))
    def followings(self, request, pk):
        paginator = self.paginator
        # select out followings for a specific user
        if GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            page = paginator.paginate_hbase(HBaseFollowing, (pk,), request)
        else:
            friendships = Friendship.objects.filter(from_user_id=pk)
            page = paginator.paginate_queryset(friendships)
        serializer = FriendshipFollowingSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @require_params(require_attrs='query_params', params=['type', 'user_id'])
    @method_decorator(ratelimit(key='user', rate='3/s', method='GET', block=True))
    def list(self, request):
        # list out followers or followings with Rest Framework Query Style
        # check query type
        if request.query_params['type'] not in ['followers', 'followings']:
            return Response(
                "Please check input. Query type need to be in ['followers', 'followings]",
                status=status.HTTP_400_BAD_REQUEST,
            )

        # query friendships
        query_type = request.query_params['type']
        user_id = request.query_params['user_id']
        if query_type == 'followers':
            friendships = Friendship.objects.filter(to_user_id=user_id)
            page = self.paginate_queryset(friendships)
            serializer = FriendshipFollowerSerializer(
                page,
                many=True,
                context={'request': request},
            )
        else:
            friendships = Friendship.objects.filter(from_user_id=user_id)
            page = self.paginate_queryset(friendships)
            serializer = FriendshipFollowingSerializer(
                page,
                many=True,
                context={'request': request},
            )

        return self.get_paginated_response(serializer.data)

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    @method_decorator(ratelimit(key='user', rate='3/s', method='POST', block=True))
    def follow(self, request, pk):
        # check if the user to follow exists
        to_user = self.get_object()
        # Friendship already existed. Raise error
        # avoid duplicated friendships in HBase
        if FriendshipService.has_followed(
                from_user_id=request.user.id,
                to_user_id=to_user.id
        ):
            return Response({
                'success': True,
                'duplicated': True,
            }, status=status.HTTP_201_CREATED)

        # Friendship not exists, creat new friendship
        serializer = FriendshipCreateSerializer(data={
            'from_user_id': request.user.id, # only logged in user can follow
            'to_user_id': pk,
        })
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        friendship = serializer.save()
        return Response({
            'success': True,
            'friendship': FriendshipCreateSerializer(friendship).data,
        }, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    @method_decorator(ratelimit(key='user', rate='5/s', method='POST', block=True))
    def unfollow(self, request, pk):
        to_user = self.get_object()
        # not support unfollow yourself
        if request.user.id == to_user.id:
            return Response({
                'success': False,
                'message': "You cannot unfollow yourself."
            }, status=status.HTTP_400_BAD_REQUEST)

        # delete the friendship
        delete = FriendshipService.unfollow(
            from_user_id=request.user.id, # only logged in user can unfollow
            to_user_id=to_user.id,
        )
        # delete as the number of objects deleted
        if not delete:
            return Response('Friendship not exists', status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': True,
            'deleted': '{}'.format(delete),
        }, status=status.HTTP_200_OK)









