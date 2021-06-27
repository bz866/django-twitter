from comments.api.serializers import (
    CommentSerializer,
    CommentSerializerForCreate,
    CommentSerializerForUpdate,
)
from comments.models import Comment
from comments.api.permissions import IsObjectOwner
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response


class CommentViewSet(viewsets.GenericViewSet):
    serializer_class = CommentSerializerForCreate
    queryset = Comment.objects.all()
    filterset_fields = ('tweet_id',)

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(),]
        elif self.action in ['update', 'destroy']:
            return [IsAuthenticated(), IsObjectOwner(),]
        elif self.action == 'list':
            return [IsAuthenticated(),]
        return [AllowAny(),]

    def create(self, request, *args, **kwargs):
        data = {
            'user_id': request.user.id,
            'tweet_id': request.data.get('tweet_id'),
            'content': request.data.get('content'),
        }

        # validate the input by CommentSerializerForCreate
        serializer = CommentSerializerForCreate(data=data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid Comment Input',
                'error': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        # save validated comment
        comment = serializer.save()
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED
        )

    def list(self, request, *args, **kwargs):
        # only return comments of the specified tweet
        if 'tweet_id' not in request.query_params:
            return Response({
                'success': False,
                'message': "missing 'tweet_id' in request"
            }, status=status.HTTP_400_BAD_REQUEST)
        # filter comments by tweet_id, and order comments by created_at time
        queryset = self.get_queryset()
        comments = self.filter_queryset(queryset)
        serializer = CommentSerializer(comments, many=True)
        return Response({
            'success': True,
            'comments': serializer.data,
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        # feed the comment instance to the serializer to update
        # if not feed instance, serializer create object
        comment = self.get_object()
        serializer = CommentSerializerForUpdate(
            data=request.data,
            instance=comment,
        )
        # validate the input of the update
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Invalid Comment Update Input',
                'error': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        # save the update
        updated_comment = serializer.save()
        return Response(
            CommentSerializer(updated_comment).data,
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()
        return Response({
            'success': True,
        }, status=status.HTTP_204_NO_CONTENT)






