from friendships.models import Friendship
from friendships.api.serializers import (
    FriendshipFollowerSerializer,
    FriendshipFollowingSerializer,
    FriendshipCreateSerializer,
)
from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status


class FriendshipViewSet(
        viewsets.GenericViewSet,
        # mixins.CreateModelMixin,
        # mixins.UpdateModelMixin,
    ):
    serializer_class = FriendshipCreateSerializer
    queryset = User.objects.all()

    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny(),]
        return [IsAuthenticated(),]

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followers(self, request, pk):
        # select out followers for a specific user
        friendships = Friendship.objects.filter(to_user_id=pk)
        serializer = FriendshipFollowerSerializer(friendships, many=True)
        return Response({'friendship': serializer.data})

    @action(methods=['GET'], detail=True, permission_classes=[AllowAny])
    def followings(self, request, pk):
        # select out followings for a specific user
        friendships = Friendship.objects.filter(from_user_id=pk)
        serializer = FriendshipFollowingSerializer(friendships, many=True)
        return Response({'friendship': serializer.data})

    def list(self, request):
        # list out followers and followings with Rest Framework Query Style
        # check query type
        if 'type' not in request.query_params:
            return Response(
                "Please check input. Query type missed.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request.query_params['type'] not in ['followers', 'followings']:
            return Response(
                "Please check input. Query type need to be in ['followers', 'followings]",
                status=status.HTTP_400_BAD_REQUEST,
            )
        # must specify the user_id for query
        if 'user_id' not in request.query_params:
            return Response(
                "Please check input. user_id need to be specified",
                status=status.HTTP_400_BAD_REQUEST,
            )

        # query friendships
        query_type = request.query_params['type']
        user_id = request.query_params['user_id']
        if query_type == 'followers':
            friendships = Friendship.objects.filter(to_user_id=user_id)
            serializer = FriendshipFollowerSerializer(friendships, many=True)
        else:
            friendships = Friendship.objects.filter(from_user_id=user_id)
            serializer = FriendshipFollowingSerializer(friendships, many=True)

        return Response({'friendship': serializer.data})

    @action(methods=['POST'], detail=True, permission_classes=[IsAuthenticated])
    def follow(self, request, pk):
        # Friendship already existed. Return success without warning
        if Friendship.objects.filter(
            from_user_id=request.user.id,
            to_user_id=pk,
        ).exists():
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
    def unfollow(self, request, pk):
        # not support unfollow yourself
        if request.user.id == int(pk):
            return Response({
                'success': False,
                'message': "You cannot unfollow yourself."
            }, status=status.HTTP_400_BAD_REQUEST)

        # delete the friendship
        delete, _ = Friendship.objects.filter(
            from_user_id=request.user.id, # only logged in user can unfollow
            to_user_id=pk,
        ).delete()
        # delete as the number of objects deleted
        if not delete:
            return Response('Friendship not exists', status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': True,
            'deleted': '{}'.format(delete),
        }, status=status.HTTP_200_OK)









