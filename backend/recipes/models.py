from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

from core.constants import MAX_COOK_TIME, MIN_COOK_TIME
from recipes.constants import (
    INGREDIENT_NAME_MAX_LENGTH,
    MEASURE_MAX_LENGTH,
    RECIPE_NAME_MAX_LENGTH,
    RECIPE_TEXT_MAX_LENGTH,
    TAG_NAME_MAX_LENGTH,
)

User = get_user_model()


class Tag(models.Model):

    name = models.CharField(
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True,
        verbose_name='Tag')
    slug = models.SlugField(
        unique=True,
        verbose_name='Slug'
    )

    class Meta:
        verbose_name_plural = 'Tags'

    def __str__(self):
        return self.name


class Ingredient(models.Model):

    name = models.CharField(
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        unique=True,
        verbose_name='Ingredient')
    measurement_unit = models.CharField(
        max_length=MEASURE_MAX_LENGTH,
        verbose_name='Measurement unit'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_measurement_unit'
            ),
        ]
        verbose_name_plural = 'Ingredients'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):

    author = models.ForeignKey(
        User,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        verbose_name='Author')
    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH,
        null=False,
        blank=False,
        help_text='Up to 50 symbols',
        verbose_name='Name')
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to='images/recipes/',
        help_text='Upload PNG or JPEG files',
        verbose_name='Image')
    text = models.TextField(
        max_length=RECIPE_TEXT_MAX_LENGTH,
        null=False,
        blank=False,
        help_text='Up to 200 symbols',
        verbose_name='Description'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        blank=False,
        through='RecipeIngredient',
        verbose_name='Ingredients'
    )
    tags = models.ManyToManyField(
        Tag,
        blank=False,
        verbose_name='Теги')
    cooking_time = models.PositiveIntegerField(
        null=False,
        blank=False,
        verbose_name='Cooking time',
        help_text='Minutes',
        validators=[MaxValueValidator(MAX_COOK_TIME),
                    MinValueValidator(MIN_COOK_TIME)]
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created')
    hash = models.CharField(
        null=True,
        blank=True,
        max_length=6,
        unique=True,
        verbose_name='Short link hash'
    )

    class Meta:
        default_related_name = 'recipes'
        verbose_name_plural = 'Recipes'
        ordering = ('-created',)
        unique_together = ('name', 'author',)

    def get_absolute_url(self):
        """Absolute path to recipe URL."""

        return reverse('recipes-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Recipe')
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ingredient')
    amount = models.FloatField(
        verbose_name='Amount',
        validators=[MinValueValidator(0.1)]
    )

    class Meta:
        verbose_name_plural = 'Recipe ingredients'
        unique_together = ('recipe', 'ingredient',)

    def __str__(self):
        return (f'{self.amount} {self.ingredient.measurement_unit} '
                f'{self.ingredient.name} for {self.recipe.name}')


class FavoriteAndCart(models.Model):

    author = models.ForeignKey(
        User,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        verbose_name='Author')
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Recipe')

    class Meta:
        abstract = True
        unique_together = ('recipe', 'author',)

    def __str__(self):
        return f'Recipe {self.recipe.name} by {self.recipe.author}'


class RecipeFavorited(FavoriteAndCart):

    class Meta(FavoriteAndCart.Meta):
        verbose_name_plural = 'Favorite recipes'
        default_related_name = 'favorite_recipes'


class ShoppingCart(FavoriteAndCart):

    class Meta(FavoriteAndCart.Meta):
        verbose_name_plural = 'Ingredients to purchase'
        default_related_name = 'cart_ingredients'
