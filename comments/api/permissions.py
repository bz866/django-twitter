from rest_framework.permissions import BasePermission


class IsObjectOwner(BasePermission):
    """
    check if the user is the owner of an object
    """
    # if detail=False, call has_permission()
    # if detail=True, call both has_permission() and has_object_permission()

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user
