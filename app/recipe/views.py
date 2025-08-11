"""
Views for the recipe app.
"""
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer, TagSerializer, IngredientSerializer, \
    RecipeImageSerializer


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma-separated list of tag IDs to filter recipes by tags.'
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma-separated list of ingredient IDs to filter recipes by ingredients.'
            )
        ]

    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    """
    Viewset for managing recipes.
    """
    serializer_class = RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_int(self, qs):
        """
        Convert a list of string IDs to a list of integers.
        """
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """
        Retrieve the recipes for the authenticated user only.
        """
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_int(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredient_ids = self._params_to_int(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)
        return queryset.filter(
            user=self.request.user
        ).order_by('-id').distinct()

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the action.
        """
        if self.action == 'list':
            return RecipeSerializer
        elif self.action == 'upload_image':
            return RecipeSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """
        Create a new recipe with the authenticated user as the owner.
        """
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """
        Upload an image for a recipe.
        """
        recipe = self.get_object()
        serializer = RecipeImageSerializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0,1],
                description='Filter by items assigned to recipes'
            )
        ]
    )
)
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
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)
        return queryset.filter(user=self.request.user).order_by('-name').distinct()

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