from typing import Any

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import View


class IsOwner(permissions.BasePermission):
    """Authorization for authors, staff, and admins."""

    def has_object_permission(
            self,
            request: Request,
            view: View,
            obj: Any) -> bool:
        """Checks access permissions for objects.

        Args:
            request (Request): The incoming request.
            view (View): The view handling the request.
            obj (Any): The object being accessed.

        Returns:
            bool: True if the user is the author, staff, or superuser.
        """

        return (obj.author == request.user
                or request.user.is_staff
                or request.user.is_superuser)


class IsOwnerOrReadOnly(IsOwner):
    """Extends IsOwner and allows safe methods
    (GET, HEAD, OPTIONS) for other users.
    """

    def has_object_permission(
            self,
            request: Request,
            view: View,
            obj: Any) -> bool:
        """Checks object permissions with condition for read-only access.

        Args:
            request (Request): The incoming request.
            view (View): The view handling the request.
            obj (Any): The object being accessed.

        Returns:
            bool: True if the user authorized or the request is a safe method.
        """

        return (super().has_object_permission(request, view, obj)
                or request.method in permissions.SAFE_METHODS)


class IsAuthenticatedOrReadOnlyOrCreateUser(
    permissions.IsAuthenticatedOrReadOnly
):
    """Extends permissions to allow anonymous users to register."""

    def has_permission(
            self,
            request: Request,
            view: View) -> bool:
        """Checks if the user is authenticated or if it's a sign-up request.

        Args:
            request (Request): The incoming request.
            view (View): The view handling the request.

        Returns:
            bool: True if the user is authenticated, it's a safe method,
            or it's a POST request.
        """

        return (super().has_permission(request, view)
                or request.method == 'POST')
