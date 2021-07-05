from rest_framework import viewsets
from likes.models import Like
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from likes.api.serializers import LikeSerializer
from likes.api.serializers import LikeSerializerForCreate
from utils.decorators import require_params
from rest_framework.response import Response
from rest_framework import status


class LikeViewSet(viewsets.GenericViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializerForCreate

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(),]
        return [AllowAny(),]

    @require_params(require_attrs='data', params=['content_type', 'object_id'])
    def create(self, request, *args, **kwargs):
        serializer = LikeSerializerForCreate(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        like = serializer.save()
        return Response({
            'success': True,
            'like': LikeSerializer(like).data
        }, status=status.HTTP_200_OK)
