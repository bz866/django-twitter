from django.utils.decorators import method_decorator
from inbox.services import NotificationService
from likes.api.serializers import LikeSerializer
from likes.api.serializers import LikeSerializerForCancel
from likes.api.serializers import LikeSerializerForCreate
from likes.models import Like
from ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utils.decorators import require_params


class LikeViewSet(viewsets.GenericViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializerForCreate

    def get_permissions(self):
        if self.action in ['create', 'cancel']:
            return [IsAuthenticated(),]
        return [AllowAny(),]

    @require_params(require_attrs='data', params=['content_type', 'object_id'])
    @method_decorator(ratelimit(key='user', rate='10/s', method='POST', block=True))
    def create(self, request):
        serializer = LikeSerializerForCreate(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        like, created = serializer.get_or_create()
        # raise notifications in creation, do not dispatch notifications if liked
        if created:
            NotificationService.send_like_notification(like)
        return Response({
            'success': True,
            'like': LikeSerializer(like).data
        }, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False)
    @require_params(require_attrs='data', params=['content_type', 'object_id'])
    @method_decorator(ratelimit(key='user', rate='10/s', method='POST', block=True))
    def cancel(self, request):
        serializer = LikeSerializerForCancel(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        deleted = serializer.cancel()
        return Response({
            'success': True,
            'deleted': deleted,
        }, status=status.HTTP_200_OK)