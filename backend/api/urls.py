from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    IngridientViewSet,
    ManageUsersViewSet,
    RecipeViewSet,
    ShortLinkRedirectView,
    TagViewSet,
    create_or_get_token,
    remove_token,
)

users_router = DefaultRouter()
recipes_router = DefaultRouter()

recipes_router.register(
    'ingredients', IngridientViewSet, basename='ingredients'
)
recipes_router.register('tags', TagViewSet, basename='tags')
recipes_router.register(
    'recipes', RecipeViewSet, basename='recipes'
)

users_router.register('users', ManageUsersViewSet, basename='users')

api_v1_urls = [
    path('auth/token/login/', create_or_get_token, name='login'),
    path('auth/token/logout/', remove_token, name='logout'),
    *users_router.urls,
    *recipes_router.urls,
]

urlpatterns = [
    path('api/', include(api_v1_urls)),
    path('s/<str:hash>/', ShortLinkRedirectView.as_view(), name='sl_redirect'),
]
