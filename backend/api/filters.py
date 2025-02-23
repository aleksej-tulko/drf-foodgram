from django.db.models import QuerySet
from django_filters import FilterSet, NumberFilter

from recipes.models import Recipe


class RecipeFilter(FilterSet):
    """Recipe filter.

    Attributes:
        is_favorited (NumberFilter): Filter favorite recipes.
        is_in_shopping_cart (NumberFilter): Filter recipes in shopping cart.

    Methods:
        filter_relation(queryset: QuerySet, related: str, value: int)
                -> QuerySet:
            Filters recipes based on a MTM relation with the current user.
        filter_is_favorited(queryset: QuerySet, name: str, value: int)
                -> QuerySet:
            Filters recipes that are marked as favorites.
        filter_is_in_shopping_cart(queryset: QuerySet, name: str, value: int)
                -> QuerySet:
            Filters recipes that are added to the shopping cart.

    Meta:
        model (Model): The Recipe model.
        fields (tuple): Fields available for filtering.
    """

    is_favorited = NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = NumberFilter(method='filter_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart',)

    def filter_relation(
            self,
            queryset: QuerySet,
            related: str,
            value: int) -> QuerySet:
        """Filters recipes based on a MTM relation.

        Used when calling /api/recipes/ endpoint.
        Applicable filters: `is_favorite` and `shopping_cart`.

        Args:
            queryset (QuerySet): The initial queryset of recipes.
            related (str): The related model name used in filtering.
            value (int): 0 to exclude or 1 to include
                        recipes associated with the request user.

        Returns:
            QuerySet: The filtered queryset.
        """

        if self.request.user.is_authenticated and value in (0, 1):
            method = queryset.filter if value == 1 else queryset.exclude
            return method(**{f'{related}__author': self.request.user})
        return queryset

    def filter_is_favorited(
            self,
            queryset: QuerySet,
            name,
            value: int) -> QuerySet:
        """Filters recipes that are marked as favorites.

        Uses method `filter_relation` to return QuerySet.
        """

        return self.filter_relation(
            queryset, 'favorite_recipes', value
        )

    def filter_is_in_shopping_cart(
            self,
            queryset: QuerySet,
            name,
            value: int) -> QuerySet:
        """Filters recipes that are added to the shopping cart.

        Uses method `filter_relation` to return QuerySet.
        """

        return self.filter_relation(
            queryset, 'cart_ingredients', value
        )
