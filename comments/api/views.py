from comments.api.serializers import CommentSerializer
from comments.api.serializers import CommentSerializerForCreate
from comments.api.serializers import CommentSerializerForUpdate
from comments.models import Comment
from django.utils.decorators import method_decorator
from inbox.services import NotificationService
from ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from utils.decorators import require_params
from utils.permissions import IsObjectOwner


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

    @method_decorator(ratelimit(key='user', rate='1/s', method='POST', block=True))
    @method_decorator(ratelimit(key='user', rate='5/m', method='POST', block=True))
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
        # raise notification for comment creation
        NotificationService.send_comment_notification(comment)
        serializer = CommentSerializer(
            instance=comment,
            context={'request': request},
        )
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @require_params(require_attrs='query_params', params=['tweet_id'])
    @method_decorator(ratelimit(key='user', rate='10/s', method='GET', block=True))
    def list(self, request, *args, **kwargs):
        # filter comments by tweet_id, and order comments by created_at time
        queryset = self.get_queryset()
        comments = self.filter_queryset(queryset)
        serializer = CommentSerializer(
            instance=comments,
            context={'request': request},
            many=True)
        return Response({
            'success': True,
            'comments': serializer.data,
        }, status=status.HTTP_200_OK)

    @method_decorator(ratelimit(key='user', rate='3/s', method='POST', block=True))
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
        serializer = CommentSerializer(
            instance=updated_comment,
            context={'request': request},
        )
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @method_decorator(ratelimit(key='user', rate='5/s', method='POST', block=True))
    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()
        return Response({
            'success': True,
        }, status=status.HTTP_204_NO_CONTENT)






