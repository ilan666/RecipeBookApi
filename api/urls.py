from django.urls import path
from rest_framework import routers
from django.conf.urls import include
from api.views import RecipeViewSet, IngredientViewSet, InstructionViewSet, RecipeIngredientViewSet, UserViewSet

router = routers.DefaultRouter()

router.register('recipes', RecipeViewSet)
router.register('ingredients', IngredientViewSet)
router.register('instructions', InstructionViewSet)
router.register('recipe_ingredient', RecipeIngredientViewSet)
router.register('users', UserViewSet)

urlpatterns = [
     path('', include(router.urls))
]