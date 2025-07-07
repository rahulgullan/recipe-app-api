"""
serializer for recipe app
"""
from rest_framework import serializers
from core.models import Recipe, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags associated with recipes."""

    class Meta:
        model = Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipe objects."""

    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ('id', 'title', 'time_minutes', 'price', 'link', 'tags')
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

    def create(self, validated_data):
        """Create a recipe"""
        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        if tags:
            self._get_or_create_tags(tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Update a recipe"""
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ('description',)
        read_only_fields = RecipeSerializer.Meta.read_only_fields

