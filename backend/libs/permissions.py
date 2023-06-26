from rest_framework import permissions


class IsAuthorized(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and hasattr(request.user, "channel"))
