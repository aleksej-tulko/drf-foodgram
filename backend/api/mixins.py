from django.contrib.auth import get_user_model
from django.db.models import Count, QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from api.serializers import ReadUserSerializer, WriteUserSerializer
from recipes.models import Recipe
from users.models import Subscription

User = get_user_model()


class IngredientAndTagReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """Viewset for reading ingredients and tags."""

    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None


class UsersAuxiliaryMixin(viewsets.ModelViewSet):
    """
    Mixin for auxiliary methods and overriding
    built-in viewset methods for user management.
    """

    def get_serializer_class(self) -> type[Serializer]:
        """Selects the appropriate serializer class."""

        return (WriteUserSerializer if self.action in ('create',)
                else ReadUserSerializer)

    def get_subscription(self, user, pk: int) -> QuerySet:
        """Gets and annotates a subscription for a given user.

        Args:
            user (User): The user making the request.
            pk (int): The ID of the user to check the subscription for.

        Returns:
            QuerySet: The subscription queryset with an annotated recipe count.
        """

        following = get_object_or_404(User, id=pk)
        return Subscription.objects.filter(
            user=user, following=following).select_related(
                'following').prefetch_related(
                    'following__recipes').annotate(
                        recipes_count=Count('following__recipes'))

    def retrieve(self, request: Request, pk: int) -> Response:
        """Retrieves a single user.

        Rewrites built-in `retrieve` method.

        Args:
            request (Request): The request object.
            pk (int): The ID of the user to retrieve.

        Returns:
            Response: The serialized user data.
        """

        user = get_object_or_404(User.objects.all(), id=pk)
        serilizer = self.get_serializer(user)
        return Response(serilizer.data, status=status.HTTP_200_OK)


class RecipesAuxiliaryMixin(viewsets.ModelViewSet):
    """
    Mixin for auxiliary methods and overriding
    built-in viewset methods for recipe management.
    """

    def get_recipe(self) -> Recipe:
        """Retrieves a single recipe based on the request's kwargs.

        Returns:
            Recipe: The requested recipe object.
        """

        return get_object_or_404(Recipe, id=self.kwargs['pk'])

    def partial_update(self, request: Request, pk: int) -> Response:
        """Updates a recipe partially.

        Rewrites built-in `partial_update` method.

        Args:
            request (Request): The request object.
            pk (int): The ID of the recipe to update.

        Returns:
            Response: The updated recipe data.
        """

        self.check_object_permissions(request, self.get_recipe())
        serializer = self.get_serializer(
            self.get_recipe(),
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
