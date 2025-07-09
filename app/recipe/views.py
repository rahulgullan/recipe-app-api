"""
Views for the recipe app.
"""
from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer, TagSerializer, IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Viewset for managing recipes.
    """
    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retrieve the recipes for the authenticated user only.
        """
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the action.
        """
        if self.action == 'list':
            return RecipeSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """
        Create a new recipe with the authenticated user as the owner.
        """
        serializer.save(user=self.request.user)


class BaseRecipeAttrViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    Base viewset for managing recipe attributes like tags and ingredients.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retrieve attributes for the authenticated user only.
        """
        return self.queryset.filter(user=self.request.user).order_by('-name')

    def perform_create(self, serializer):
        """
        Create a new attribute with the authenticated user as the owner.
        """
        serializer.save(user=self.request.user)


class TagViewSet(BaseRecipeAttrViewSet):
    """
    Viewset for managing tags associated with recipes.
    """
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    """
    Viewset for managing ingredients associated with recipes.
    """
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()