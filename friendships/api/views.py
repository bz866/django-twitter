from friendships.models import Friendship
from friendships.api.serializers import FriendshipFollowerSerializer, FriendshipFollowingSerializer
from accounts.api.serializer import UserSerializerForFriendship
from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status


class FriendshipViewSet(
        viewsets.GenericViewSet,
        mixins.ListModelMixin,
        mixins.CreateModelMixin,
        mixins.UpdateModelMixin,
    ):
    serializer_class = UserSerializerForFriendship
    queryset = Friendship.objects.all()

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
        friendships = Friendship.objects.filter(from_user_id=pk)
        serializer = FriendshipFollowingSerializer(friendships, many=True)
        return Response({'friendship': serializer.data})

    def list(self, request):
        # check query type
        if 'type' not in request.query_params:
            return Response(
                "Please check input. Query type missed.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request.query_params['type'] not in ['follower', 'following']:
            return Response(
                "Please check input. Query type need to be in ['follower', 'following]",
                status=status.HTTP_400_BAD_REQUEST,
            )
        # must specify the user_id for query
        if 'user_id' not in request.query_params:
            return Response(
                "Please check input. user_id need to be specified",
                status=status.HTTP_400_BAD_REQUEST,
            )

        # query friendships
        type = request.query_params['type']
        user_id = request.query_params['user_id']
        if type == 'follower':
            friendships = Friendship.objects.filter(to_user_id=user_id)
            serializer = FriendshipFollowerSerializer(friendships, many=True)
        else:
            friendships = Friendship.objects.filter(from_user_id=user_id)
            serializer = FriendshipFollowingSerializer(friendships, many=True)

        return Response({'friendship': serializer.data})




