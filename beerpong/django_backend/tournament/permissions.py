from rest_framework.permissions import BasePermission


class IsOrga(BasePermission):
    """Allows access only to users with is_orga=True (or staff)."""
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_orga or request.user.is_staff)
        )


class IsOrgaOrLiveview(BasePermission):
    """Allows access to orga users AND liveview users."""
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_orga or request.user.is_liveview or request.user.is_staff)
        )
