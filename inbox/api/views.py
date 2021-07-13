from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from inbox.api.serializers import NotificationSerializer
from inbox.api.serializers import NotificationSerializerForUpdate
from notifications.models import Notification
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from utils.decorators import require_params


class NotificationViewSet(GenericViewSet, ListModelMixin,):

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated,]
    filter_fields = ('unread', )

    def get_queryset(self):
        """
        override the query_set,
        Only show user related notifications for LIST method
        """
        return Notification.objects.filter(recipient=self.request.user)

    @action(methods=['GET'], detail=False, url_path='unread-count')
    def unread_count(self, request):
        """
        count all unread notifications of a user
        """
        count = Notification.objects.filter(
            recipient=self.request.user,
            unread=True,
        ).count()
        return Response({'count': count}, status=status.HTTP_200_OK)

    @action(methods=['PUT'], detail=False, url_path='mark-all-as-read')
    def mark_all_as_read(self, request, *args, **kwargs):
        """
        mark all unread notifications to read if there is any
        """
        notifications = Notification.objects.filter(
            recipient=self.request.user,
            unread=True,
        )
        # update notification status
        updated_count = notifications.update(unread=False)
        return Response({
            'updated_count': updated_count
        }, status=status.HTTP_200_OK)

    @require_params(require_attrs='data', params=['unread'])
    def update(self, request, *args, **kwargs):
        notification = self.get_object()
        serializer = NotificationSerializerForUpdate(
            data=request.data,
            instance=notification,
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Please check the input',
                'error': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        updated_notification = serializer.save()
        return Response({
            'success': True,
            'notification': NotificationSerializer(updated_notification).data,
        }, status=status.HTTP_200_OK)