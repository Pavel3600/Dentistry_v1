from rest_framework.permissions import BasePermission, SAFE_METHODS


def _role(user):
    return getattr(getattr(user, 'profile', None), 'role', 'patient')


class IsAdminRole(BasePermission):
    message = 'Доступ разрешён только администраторам.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and _role(request.user) == 'admin'


class IsManagerOrAdmin(BasePermission):
    message = 'Доступ разрешён менеджерам и администраторам.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and _role(request.user) in ('manager', 'admin')


class IsDentistOrAdmin(BasePermission):
    message = 'Доступ разрешён стоматологам и администраторам.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and _role(request.user) in ('dentist', 'admin')


class IsManagerDentistOrAdmin(BasePermission):
    message = 'Доступ разрешён менеджерам, стоматологам и администраторам.'

    def has_permission(self, request, view):
        return request.user.is_authenticated and _role(request.user) in ('manager', 'dentist', 'admin')


class ReadOnlyOrAdmin(BasePermission):
    """Allow read for any authenticated user; write only for admin."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return _role(request.user) == 'admin'
