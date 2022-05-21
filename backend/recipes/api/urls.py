from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (RecipeViewSet, UserViewSet, get_token, delete_token,
                    TagViewSet, CartView, FollowView, IngredientViewSet,)

router_v1 = DefaultRouter()
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('users', UserViewSet, basename='users')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')


auth = [
    path('login/', get_token, name='get_token'),
    path('logout/', delete_token, name='delete_token'),
]

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/token/', include(auth)),
    path('recipes/<pk>/<str:action>/', CartView.as_view()),
    path('users/<pk>/subscribe/', FollowView.as_view()),
]
