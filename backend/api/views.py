from collections import defaultdict

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.db.models import Count, Model, QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.utils.crypto import get_random_string
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import filters, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from api.constants import (
    PASSWORD_NAME,
    PASSWORD_URI,
    PDF_NAME,
    PDF_URI,
    SHORT_LINK_NAME,
    SHORT_LINK_URI,
    SUBSCRIPTIONS_NAME,
    SUBSCRIPTIONS_URI,
    USERS_FILTER,
    USERS_SEARCH,
)
from api.filters import RecipeFilter
from api.mixins import (
    IngredientAndTagReadOnlyViewSet,
    RecipesAuxiliaryMixin,
    UsersAuxiliaryMixin,
)
from api.pagination import FoodgramRecipeUserPagination
from api.permissions import (
    IsAuthenticatedOrReadOnlyOrCreateUser,
    IsOwner,
    IsOwnerOrReadOnly,
)
from api.serializers import (
    AvatarSerializer,
    ChangePasswordSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    TagSerializer,
)
from api.validators import regex_email
from core.constants import USERS_ORDER
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeFavorited,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription

User = get_user_model()

USER_NO_AVATAR = 'User {} does not have avatar.'
EMPTY_CART = 'The shopping cart is empty.'
LIMIT_ERROR = 'Set correct limit.'


class ManageUsersViewSet(UsersAuxiliaryMixin):
    """
    A ViewSet for managing user-related operations such as retrieving,
    creating, updating, and deleting users.

    This ViewSet supports the following HTTP methods:
    - GET: Retrieve a list of users or a single user.
    - POST: Create a new user.
    - PUT: Update an existing user.
    - DELETE: Remove a user.

    It uses the following configurations:
    - Permissions: The user must be authenticated or the request must be
    for reading or creating a user.
    - Pagination: Users are paginated using the `FoodgramRecipeUserPagination`
    class.
    - Filtering: Users can be filtered by fields defined in `USERS_FILTER` and
    can search based on `USERS_SEARCH`.
    - Ordering: Users can be ordered based on fields defined in `USERS_ORDER`.

    This ViewSet ensures efficient user management and access control
    in the application.
    """

    http_method_names = ('get', 'post', 'delete', 'put',)
    permission_classes = (IsAuthenticatedOrReadOnlyOrCreateUser,)
    queryset = User.objects.all()
    pagination_class = FoodgramRecipeUserPagination
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = USERS_FILTER
    search_fields = USERS_SEARCH
    ordering_fields = USERS_ORDER

    @action(detail=False, url_path=settings.AVATAR_PAGE_URL,
            url_name=settings.AVATAR_PAGE_URL)
    def avatar(self) -> None:
        """Decorator for avatar management."""

    @action(detail=True, permission_classes=(IsAuthenticated,))
    def subscribe(self) -> None:
        """Decorator for managing subscriptions."""

    @action(detail=False, url_path=settings.PERSONAL_PAGE_URL,
            url_name=settings.PERSONAL_PAGE_URL,
            permission_classes=(IsAuthenticated,),
            methods=('GET',))
    def get_personal_page(self, request: Request) -> Response:
        """
        Retrieve the authenticated user's personal profile details.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: Serialized user data with a 200 status code.
        """

        return Response(
            self.get_serializer(request.user).data, status=status.HTTP_200_OK
        )

    @avatar.mapping.put
    def add_avatar(self, request: Request) -> Response:
        """
        Upload or update the authenticated user's avatar.

        Args:
            request (Request): The HTTP request object containing image data.

        Returns:
            Response: Serialized avatar data with a 200 status code.
        """

        serializer = AvatarSerializer(
            instance=request.user,
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request: Request) -> Response:
        """
        Delete the authenticated user's avatar.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: Empty response with a 204 status code.
        """

        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @subscribe.mapping.post
    def add_subscription(self, request: Request, pk: int) -> Response:
        """
        Subscribe the authenticated user to another user.

        Args:
            request (Request): The HTTP request object.
            pk (int): The ID of the user to subscribe to.

        Returns:
            Response: Subscription details with a 201 status code.
        """

        subscription = self.get_subscription(user=request.user, pk=pk)
        serializer = SubscriptionSerializer(
            data={'following': pk},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        following = subscription.get().following
        response_data = {
            **serializer.data,
            'id': following.id,
            'first_name': following.first_name,
            'last_name': following.last_name,
            'username': following.username,
            'email': following.email,
            'is_subscribed': True,
            'recipes_count': subscription.get().recipes_count
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscription(self, request: Request, pk: int) -> Response:
        """
        Unsubscribe the authenticated user from another user.

        Args:
            request (Request): The HTTP request object.
            pk (int): The ID of the user to unsubscribe from.

        Returns:
            Response: Empty response with a 204 status code if successful,
            400 status code if the subscription does not exist.
        """

        subscription = self.get_subscription(user=request.user, pk=pk)
        if subscription:
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False, url_path=SUBSCRIPTIONS_URI, url_name=SUBSCRIPTIONS_NAME,
        permission_classes=(IsAuthenticated,), methods=('get',)
    )
    def list_subscriptions(self, request: Request, pk=None) -> Response:
        """
        Retrieve a list of users the authenticated user is subscribed to.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Response: Paginated list of subscriptions.
        """

        subscriptions = (
            Subscription.objects.filter(user=request.user).prefetch_related(
                'following').annotate(recipes_count=Count(
                    'following__recipes')).order_by('following__username')
        )
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(subscriptions, request)
        serializer = SubscriptionSerializer(
            result_page, context={'request': request}, many=True
        )
        response_data = [
            {**data,
             'recipes_count': subscription.recipes_count,
             'first_name': subscription.following.first_name,
             'last_name': subscription.following.last_name,
             'username': subscription.following.username,
             'email': subscription.following.email,
             'is_subscribed': True,
             'id': subscription.following.id}
            for data, subscription in zip(serializer.data, result_page)
        ]
        return paginator.get_paginated_response(response_data)

    @action(
        detail=False, url_path=PASSWORD_URI, url_name=PASSWORD_NAME,
        permission_classes=(IsAuthenticated,), methods=('post',)
    )
    def change_password(self, request: Request, pk=None) -> Response:
        """
        Change the authenticated user's password.

        Args:
            request (Request): The HTTP request object containing
            old and new passwords.

        Returns:
            Response: Empty response with a 204 status code.
        """

        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.update(request.user, serializer.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes((IsAuthenticatedOrReadOnlyOrCreateUser,))
def create_or_get_token(request: Request) -> Response:
    """
    Generate or retrieve an authentication token for a user.

    Args:
        request (Request): The HTTP request object containing
        email and password.

    Returns:
        Response: Authentication token if credentials are valid,
        400 status code otherwise.
    """

    if 'email' in request.data and 'password' in request.data:
        password = request.data['password']
        email = regex_email(email=request.data['email'])
        user = get_object_or_404(User.objects.filter(email=email))
        auth_user = authenticate(email=user.email, password=password)
        token, _ = Token.objects.get_or_create(user=auth_user)
        return Response({'auth_token': token.key}, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def remove_token(request: Request) -> Response:
    """
    Remove the authentication token of the authenticated user.

    Args:
        request (Request): The HTTP request object.

    Returns:
        Response: Empty response with a 204 status code.
    """

    request.user.auth_token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


class IngridientViewSet(IngredientAndTagReadOnlyViewSet):
    """
    ViewSet for retrieving ingredient data.

    This ViewSet handles operations for retrieving ingredient details with
    optional search and filtering.

    HTTP methods supported:
    - GET: Retrieve a list of ingredients or a specific ingredient.

    Configurations:
    - Serializer: The `IngredientSerializer` is used for serializing
    ingredient data.
    - Filtering: Ingredients can be filtered by name using the `name` field.
    - Searching: Ingredients can be searched by their name.

    This ViewSet allows users to efficiently access and filter ingredients
    based on their name.
    """

    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)

    def get_queryset(self) -> QuerySet:
        """
        Retrieves the ingredient queryset with optional filtering.

        If a search query is provided, ingredients that start with
        the search term will be prioritized, followed by other matches
        that contain the term.

        Returns:
            QuerySet: Sorted list of ingredients.
        """

        queryset = Ingredient.objects.all().order_by('name')
        name = self.request.query_params.get('name')
        if name:
            first_match_qs = queryset.filter(name__istartswith=name)
            first_match_items = first_match_qs.values_list('name')
            other_match_qs = queryset.filter(
                name__icontains=name).exclude(name__in=first_match_items)
            return tuple(first_match_qs) + tuple(other_match_qs)
        return queryset


class TagViewSet(IngredientAndTagReadOnlyViewSet):
    """
    ViewSet for retrieving tag data.

    This ViewSet handles the retrieval of tag information.

    HTTP methods supported:
    - GET: Retrieve a list of tags.

    Configurations:
    - Serializer: The `TagSerializer` is used to serialize the tag data.

    This ViewSet allows users to access tag information efficiently.
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(RecipesAuxiliaryMixin):
    """
    ViewSet for managing recipes and related operations.

    This ViewSet supports a variety of recipe-related actions, including
    filtering, searching, favoriting, adding to shopping cart, generating
    shopping lists, and creating short links.

    HTTP methods supported:
    - GET: Retrieve a list of recipes or a specific recipe.
    - POST: Create a new recipe.
    - PUT: Update an existing recipe.
    - DELETE: Delete a recipe.
    - GET (action): Generate a short link for a recipe.
    - GET (action): Download a PDF shopping list.

    Configurations:
    - Permissions: Access is controlled by user authentication and ownership.
    - Pagination: Uses `FoodgramRecipeUserPagination` to paginate recipe list.
    - Filter: Recipes can be filtered by various parameters via `RecipeFilter`.
    - Search: Recipes can be searched by name using `search_fields`.
    - Actions: Adds actions for favoriting recipes and managing shopping cart.

    This ViewSet provides a comprehensive set of features for recipe management
    and interaction with user-specific collections such as favorites and
    shopping carts.
    """

    queryset = Recipe.objects.all().select_related(
        'author').prefetch_related(
            'ingredients', 'tags', 'favorite_recipes', 'cart_ingredients'
    )
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    pagination_class = FoodgramRecipeUserPagination
    filterset_class = RecipeFilter
    search_fields = ('name',)

    @action(
        detail=True, url_path=SHORT_LINK_URI,
        url_name=SHORT_LINK_NAME, methods=('get',)
    )
    def get_link(self, request: Request, pk=None) -> Response:
        """
        Generate a short link for a recipe.

        Args:
            request (Request): The incoming HTTP request.
            pk (int, optional): Recipe ID.

        Returns:
            Response: Shortened URL for the recipe.
        """

        recipe = self.get_recipe()
        recipe.hash = get_random_string(length=3)
        recipe.save()
        short_link_url = request.build_absolute_uri(f'/s/{recipe.hash}/')
        return Response(
            {'short-link': short_link_url}, status=status.HTTP_200_OK
        )

    @action(
        detail=False, url_path=PDF_URI, url_name=PDF_NAME,
        permission_classes=(IsOwner,), methods=('get',)
    )
    def download_pdf(self, request: Request, pk=None) -> Response:
        """
        Generate and download a PDF of the shopping cart.

        Args:
            request (Request): The incoming HTTP request.
            pk (int, optional): Not used.

        Returns:
            Response: PDF file or 404 error if cart is empty.
        """

        recipes = ShoppingCart.objects.prefetch_related('recipe').filter(
            author=self.request.user
        )
        if recipes:
            font_name = 'DejaVuSans'
            font_path = 'DejaVuSans.ttf'
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            response = HttpResponse(content_type='application/pdf')
            p = canvas.Canvas(response, pagesize=A4)
            width, height = A4
            p.setFont(font_name, 16)
            p.drawString(100, height - 50, '')
            p.setFont(font_name, 12)
            y_position = height - 100
            ingredient_dict: defaultdict = defaultdict(
                lambda: {'amount': 0, 'unit': ''})
            for recipe in recipes:
                ingredients = (
                    RecipeIngredient.objects.prefetch_related(
                        'ingredient').filter(recipe=recipe.recipe)
                )
                for ingredient in ingredients:
                    ingredient_data = ingredient_dict[
                        ingredient.ingredient.name]
                    ingredient_data['amount'] += ingredient.amount
                    ingredient_data['unit'] = (
                        ingredient.ingredient.measurement_unit)
            shopping_list = p.beginText(100, y_position)
            shopping_list.setFont(font_name, 12)
            for name, data in ingredient_dict.items():
                shopping_list.textLine(
                    f'{name} — {data["amount"]} {data["unit"]}'
                )
            p.drawText(shopping_list)
            y_position -= 20
            if y_position < 50:
                p.showPage()
                y_position = height - 50
            p.save()
            return response
        return Response(EMPTY_CART, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, permission_classes=(IsAuthenticated,))
    def favorite(self) -> None:
        """Decorator for adding and removing recipe from favorites."""

    @action(detail=True, permission_classes=(IsAuthenticated,))
    def shopping_cart(self) -> None:
        """Decorator for adding and removing recipe from the shopping cart."""

    def add_recipe(
            self,
            serializer: Serializer,
            request: Request) -> Response:
        """
        Save a recipe to a collection (favorites or shopping cart).

        Args:
            serializer (Serializer): The serializer to use.
            request (Request): The incoming HTTP request.

        Returns:
            Response: Serialized data or validation error.
        """

        serializer = serializer(
            data={'recipe': self.get_recipe(), 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user, recipe_id=self.get_recipe().id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_recipe(
            self,
            model: Model,
            request: Request) -> Response:
        """
        Remove a recipe from a collection (favorites or shopping cart).

        Args:
            model (Model): The model to remove from.
            request (Request): The incoming HTTP request.

        Returns:
            Response: 204 if deleted, 400 otherwise. 404 if a recipe not found.
        """

        recipe = model.objects.filter(
            author=request.user, recipe_id=self.get_recipe())

        if recipe:
            recipe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @favorite.mapping.post
    def add_to_favorite(self, request: Request, pk: int) -> Response:
        """Add recipe to favorites."""

        return self.add_recipe(FavoriteSerializer, request=request)

    @favorite.mapping.delete
    def delete_from_favorite(self, request: Request, pk: int) -> Response:
        """Remove recipe from favorites."""

        return self.delete_recipe(RecipeFavorited, request)

    @shopping_cart.mapping.post
    def add_to_shopping_cart(self, request: Request, pk: int) -> Response:
        """Add recipe to shopping cart."""

        return self.add_recipe(ShoppingCartSerializer, request=request)

    @shopping_cart.mapping.delete
    def delete_from_shopping_cart(self, request: Request, pk: int) -> Response:
        """Remove recipe from shopping cart."""

        return self.delete_recipe(ShoppingCart, request)


@permission_classes((AllowAny,))
class ShortLinkRedirectView(APIView):
    """View for redirecting short links to full recipe URLs."""

    def get(self, request: Request, hash: str) -> HttpResponseRedirect:
        """
        Redirect to the full recipe URL.

        Args:
            request (Request): The incoming HTTP request.
            hash (str): Short link hash.

        Returns:
            HttpResponseRedirect: Redirect response.
        """

        sl = get_object_or_404(Recipe, hash=hash)
        return redirect(sl.get_absolute_url())
