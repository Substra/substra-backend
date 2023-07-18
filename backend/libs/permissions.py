from rest_framework import permissions

from organization.authentication import OrganizationUser


class IsAuthorized(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            (
                request.user
                and request.user.is_authenticated
                and (hasattr(request.user, "channel") or isinstance(request.user, OrganizationUser))
            )
        )
