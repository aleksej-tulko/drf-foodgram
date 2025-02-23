from typing import List

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from api.constants import (
    GET_USER_FIELDS,
    NESTED_RECIPE_FIELDS,
    POST_USER_FIELDS,
    RECIPE_FIELDS,
    SUBSCRIPTION_FIELDS,
)
from api.validators import (
    check_ingredients_or_tags,
    invalid_cooking_time,
    prohibited_recipe_description,
    prohibited_recipe_name,
    prohibited_usernames,
    regex_recipe_name,
    regex_username,
)
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeFavorited,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import FoodgramUser, Subscription

User = get_user_model()

ALREADY_SUBSCRIBED = 'You are already subscribed.'
MIN_AMOUNT_ERROR = 'The minimum allowed value is 1.'
BASE64_ENCODED_IMAGE_EXPECTED = 'A Base64-encoded image string is expected.'
SELF_SUBSCRIPTION = 'You cannot subscribe to yourself.'
INCORRECT_CURRENT_PASSWORD = 'Incorrect current password.'
NEW_PASSWORD_IS_SAME = 'The new password must not be the same as the old one.'
INGREDIENT_NON_EXISTING = 'Ingredient with ID {} not found.'
NO_IMAGE_PROVIDED = 'The image field is empty.'
RECIPE_EXISTS = 'A recipe with the name {} already exists.'
RECIPE_ALREADY_ADDED = 'The recipe has already been added to the {} table.'


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing user password."""

    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate(self, data: dict) -> dict:
        """Validates password fields."""

        user = self.context['request'].user
        if not user.check_password(data['current_password']):
            raise serializers.ValidationError(INCORRECT_CURRENT_PASSWORD)
        if data['new_password'] == data['current_password']:
            raise serializers.ValidationError(NEW_PASSWORD_IS_SAME)
        return data

    def update(self,
               instance: FoodgramUser,
               validated_data: dict) -> FoodgramUser:
        """Updates user password."""

        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance


class ReadUserSerializer(serializers.ModelSerializer):
    """User serializer for read operations."""

    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj: FoodgramUser) -> bool:
        """Returns whether the user is subscribed."""

        request = self.context.get('request')
        if not request.user.is_anonymous:
            return Subscription.objects.filter(
                user_id=request.user.id, following_id=obj.id
            ).exists()
        return False

    class Meta:
        model = User
        fields = GET_USER_FIELDS + ('is_subscribed',)


class WriteUserSerializer(serializers.ModelSerializer):
    """User serializer for write operations."""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = POST_USER_FIELDS

    def validate_username(self, username: str) -> str:
        """Validates username."""

        prohibited_usernames(username)
        regex_username(username)
        return username

    def create(self, validated_data: dict) -> FoodgramUser:
        """Creates a new user with a hashed password."""

        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        user.password = password
        return user


class AvatarSerializer(serializers.ModelSerializer):
    """Serializer for handling user avatars."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, data: dict) -> dict:
        """Validates the avatar field to ensure it's Base64-encoded."""

        encoded_data = self.context['request'].data['avatar']
        if not encoded_data.startswith('data:image'):
            raise serializers.ValidationError(BASE64_ENCODED_IMAGE_EXPECTED)
        return data


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for user subscriptions."""

    recipes = serializers.SerializerMethodField()
    avatar = serializers.ImageField(
        source='following.avatar', read_only=True
    )
    following = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True
    )

    class Meta:
        model = Subscription
        fields = SUBSCRIPTION_FIELDS

    def get_recipes(self, obj: FoodgramUser) -> List[dict]:
        """Returns a limited list of recipes."""

        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit')
        recipes = Recipe.objects.filter(author=obj.following)
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeSubscriptionSerializer(recipes, many=True).data

    def validate_following(self, following: FoodgramUser) -> Subscription:
        """Validates subscription constraints."""

        request = self.context.get('request')
        if request.user == following:
            raise serializers.ValidationError(SELF_SUBSCRIPTION)
        if Subscription.objects.filter(
            user=request.user, following=following
        ).exists():
            raise serializers.ValidationError(ALREADY_SUBSCRIBED)
        return following

    def create(self, validated_data: dict) -> Subscription:
        """Creates a new subscription."""

        request = self.context.get('request')
        request.user = self.context['request'].user
        following = validated_data.get('following')
        return Subscription.objects.create(
            user=request.user, following=following
        )


class RecipeIngredientCreateSerializer(serializers.Serializer):
    """Serializer for displaying recipe ingredients."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient',
        error_messages={'does_not_exist':
                        INGREDIENT_NON_EXISTING.format('{pk_value}')})
    amount = serializers.IntegerField(
        min_value=1, error_messages={'min_value': MIN_AMOUNT_ERROR}
    )


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer ingredients."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeResponseSerializer(serializers.ModelSerializer):
    """Serializer for displaying recipes."""

    author = ReadUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_favorited(self, obj: Recipe) -> bool:
        """Checks if the recipe is in the user's favorites."""

        request = self.context.get('request')
        if request.user.is_authenticated:
            return obj.favorite_recipes.filter(
                author=request.user, recipe_id=obj.id).exists()
        return False

    def get_is_in_shopping_cart(self, obj: Recipe) -> bool:
        """Checks if the recipe is in the user's shopping cart."""

        request = self.context.get('request')
        if request.user.is_authenticated:
            return obj.cart_ingredients.filter(
                author=request.user, recipe_id=obj.id).exists()
        return False

    def get_ingredients(self, obj: Recipe) -> List[dict]:
        """Returns a list of ingredients for the recipe."""

        ingredients = RecipeIngredient.objects.filter(recipe=obj)

        return [
            {
                'id': item.ingredient.id,
                'name': item.ingredient.name,
                'measurement_unit': item.ingredient.measurement_unit,
                'amount': item.amount,
            } for item in ingredients]

    def get_tags(self, obj: Recipe) -> List[dict]:
        """Returns a list of tags for the recipe."""

        return TagSerializer(obj.tags.all(), many=True).data

    class Meta:
        model = Recipe
        fields = RECIPE_FIELDS + ('id', 'is_favorited', 'is_in_shopping_cart',)


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for handling recipes."""

    author = ReadUserSerializer(read_only=True)
    image = Base64ImageField(required=True)
    ingredients = RecipeIngredientCreateSerializer(many=True, write_only=True)
    text = serializers.CharField(required=True)
    tags = serializers.ListField(
        child=serializers.SlugRelatedField(
            queryset=Tag.objects.all(),
            slug_field='slug'), write_only=True)

    class Meta:
        model = Recipe
        fields = RECIPE_FIELDS

    def validate_cooking_time(self, time: int) -> int:
        """Validates the cooking time."""

        invalid_cooking_time(time)
        return time

    def validate_name(self, name: str) -> str:
        """Validates the recipe name."""

        prohibited_recipe_name(name)
        regex_recipe_name(name)
        return name

    def validate_text(self, text: str) -> str:
        """Validates the recipe description."""

        prohibited_recipe_description(text)
        return text

    def validate_image(self, image: str) -> SimpleUploadedFile:
        """Validates if image was provided."""

        if not image:
            raise serializers.ValidationError(NO_IMAGE_PROVIDED)
        return image

    def get_is_favorited(self, recipe: Recipe) -> Recipe:
        """Returns whether the recipe is favorited by the user."""

        return recipe.favorite_recipes

    def get_is_in_shopping_cart(self, recipe: Recipe) -> Recipe:
        """Returns whether the recipe is in the shopping cart."""

        return recipe.cart_ingredients

    def validate(self, data: dict) -> dict:
        """
        Validates that the recipe is unique for the author.
        Ensures the presence and uniqueness of tags and ingredients.
        """

        recipe_name = self.context['request'].data['name']
        tags_list = self.initial_data.get('tags', None)
        ingredients_list = self.initial_data.get('ingredients', None)
        if Recipe.objects.filter(
            name=recipe_name,
            author=self.context['request'].user
        ).exists():
            raise serializers.ValidationError(
                RECIPE_EXISTS.format(recipe_name)
            )
        check_ingredients_or_tags(tags=tags_list, ingredients=ingredients_list)
        return data

    def create(self, validated_data: dict) -> Recipe:
        """Creates and saves a new recipe."""

        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        self._create_ingredients(ingredients_data, recipe)
        recipe.tags.set(tags_data)
        return recipe

    def update(self, instance: Recipe, validated_data: dict) -> Recipe:
        """Updates an existing recipe."""

        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        instance.ingredients.clear()
        self._create_ingredients(ingredients_data, instance)
        instance.tags.set(tags_data)
        instance.save()
        return instance

    def to_representation(self, instance: Recipe) -> dict:
        """Returns the serialized representation of the recipe."""

        return RecipeResponseSerializer(
            instance, context={'request': self.context.get('request')}
        ).data

    @staticmethod
    def _create_ingredients(ingredients_data: List[dict],
                            recipe: Recipe) -> None:
        """Creates and associates ingredients with a recipe."""

        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)


class ShortRecipeDescriptionSerializer(serializers.ModelSerializer):
    """Serializer for short recipe representation."""

    name = serializers.CharField(read_only=True)
    image = Base64ImageField(read_only=True)
    cooking_time = serializers.IntegerField(read_only=True)

    class Meta:
        model = Recipe
        fields = NESTED_RECIPE_FIELDS


class FavoriteAndShoppingCartSerializer(serializers.ModelSerializer):
    """Mixin serializer for favorite recipes and shopping cart."""

    def validate(self, data: dict) -> dict:
        """
        Validates duplicates to prevent adding the same recipe multiple times.
        """

        request = self.initial_data.get('request')
        recipe = self.initial_data.get('recipe')
        model = self.Meta.model

        if model.objects.filter(author=request.user, recipe=recipe).exists():
            raise serializers.ValidationError(
                RECIPE_ALREADY_ADDED.format(model._meta.verbose_name)
            )
        return data

    def to_representation(self, instance: Recipe) -> dict:
        return ShortRecipeDescriptionSerializer(instance.recipe).data


class FavoriteSerializer(FavoriteAndShoppingCartSerializer):
    """Serializer for favorite recipes."""

    class Meta:
        model = RecipeFavorited
        fields = ('recipe',)
        read_only_fields = ('recipe',)


class ShoppingCartSerializer(FavoriteAndShoppingCartSerializer):
    """Serializer for shopping cart items."""

    class Meta:
        model = ShoppingCart
        fields = ('recipe',)
        read_only_fields = ('recipe',)


class RecipeSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for following recipes."""

    class Meta:
        model = Recipe
        fields = NESTED_RECIPE_FIELDS
