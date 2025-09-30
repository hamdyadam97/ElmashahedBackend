from rest_framework.permissions import IsAuthenticated


class IsActiveUser(IsAuthenticated):
    def has_permission(self, request, view):
        return True
