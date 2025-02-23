from itertools import chain

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from recipes.models import (
    Ingredient,
    Recipe,
    RecipeFavorited,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = tuple(
        chain(
            ('id', 'name', 'measurement_unit'),
        )
    )
    list_editable = (
        'name',
        'measurement_unit',)
    list_filter = ('measurement_unit',)
    search_fields = ('name',)
    ordering = ('id',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = tuple(
        chain(
            ('id', 'name', 'slug'),
        )
    )
    list_editable = (
        'name',
        'slug',)
    list_filter = ('name',)
    search_fields = ('name',)
    ordering = ('id',)


class RecipeInline(admin.TabularInline):
    model = Recipe.ingredients.through
    verbose_name = 'Ingredient'
    verbose_name_plural = 'Ingredients'
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):

    list_display = tuple(
        chain(
            ('id', 'recipe_image', 'name', 'author',),
        )
    )

    list_editable = ('name',)
    list_filter = ('author', 'tags')
    search_fields = ('name', 'author__username')
    ordering = ('id',)
    fieldsets = (
        ('Main Information', {
            'fields': ('name', 'author', 'cooking_time',
                       'tags', 'image', 'get_is_favorited',),
        }),
        ('Additional Information', {
            'fields': ('text', 'recipe_image',),
        }),
    )
    add_fieldsets = fieldsets
    readonly_fields = ('recipe_image', 'get_is_favorited',)
    inlines = (RecipeInline,)

    def recipe_image(self, obj):
        return format_html(
            '<img src="{}" \
                style="max-width: 300px; max-height: 300px;" />',
            obj.image.url
        )
    recipe_image.short_description = 'Photo'

    def get_is_favorited(self, obj):
        return RecipeFavorited.objects.filter(recipe=obj).count()
    get_is_favorited.short_description = 'Added to Favorites'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = tuple(
        chain(
            ('recipe', 'author',),
        )
    )
    list_filter = ('author',)
    search_fields = ('recipe',)
    ordering = ('author',)
    fieldsets = (
        ('Ingredients to purchase', {
            'fields': ('get_ingredients',),
        }),
    )
    readonly_fields = ('get_ingredients',)

    def get_ingredients(self, obj):

        return mark_safe('<br>'.join(
            f'{item.ingredient.name}: {item.amount}'
            f'{item.ingredient.measurement_unit}'
            for item in RecipeIngredient.objects.filter(recipe=obj.recipe)
        ))
    get_ingredients.short_description = 'Shopping List'


@admin.register(RecipeFavorited)
class RecipeFavoritedAdmin(admin.ModelAdmin):
    list_display = tuple(
        chain(
            ('author', 'recipe',),
        )
    )
    list_filter = ('author',)
    search_fields = ('author',)
    ordering = ('author',)
    fieldsets = (
        ('Favorites', {
            'fields': ('get_favorite',),
        }),
    )
    readonly_fields = ('get_favorite',)

    def get_favorite(self, obj):
        return mark_safe('<br>'.join(
            f'{item.recipe}' for item in
            obj.author.favorite_recipes.all()
        ))
    get_favorite.short_description = 'Like it!'
