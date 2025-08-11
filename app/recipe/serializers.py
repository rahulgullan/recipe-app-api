"""
serializer for recipe app
"""
from rest_framework import serializers
from core.models import Recipe, Tag, Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredients associated with recipes."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name')
        read_only_fields = ('id',)

    def create(self, validated_data):
        """Create an ingredient"""
        return Ingredient.objects.create(**validated_data)


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags associated with recipes."""

    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe objects."""

    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ('id', 'title', 'time_minutes', 'price', 'link', 'tags', 'ingredients')
        read_only_fields = ('id',)

    def _get_or_create_tags(self, tags, recipe):
        """Handle getting or creating  tags needed"""
        auth_user = self.context['request'].user
        for tag_data in tags:
            tag, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag_data
            )
            recipe.tags.add(tag)

    def _get_or_create_ingredients(self, ingredients, recipe):
        """Handle getting or creating ingredients needed"""
        auth_user = self.context['request'].user
        for ingredient_data in ingredients:
            ingredient, created = Ingredient.objects.get_or_create(
                user=auth_user,
                **ingredient_data
            )
            recipe.ingredients.add(ingredient)

    def create(self, validated_data):
        """Create a recipe"""
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
        if tags:
            self._get_or_create_tags(tags, recipe)
        if ingredients:
            self._get_or_create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Update a recipe"""
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ('description', 'image')
        read_only_fields = RecipeSerializer.Meta.read_only_fields


class RecipeImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to recipes."""

    class Meta:
        model = Recipe
        fields = ('id', 'image')
        read_only_fields = ('id',)
        extra_kwargs = {'image': {'required': 'True'}}

    # def update(self, instance, validated_data):
    #     """Update the recipe image"""
    #     instance.image = validated_data.get('image', instance.image)
    #     instance.save()
    #     return instance
