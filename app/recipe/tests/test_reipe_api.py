"""Test for recipe API"""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from recipe.models import Recipe
from recipe.serializers import RecipeSerializer

CREATE_RECIPE_URL = reverse('recipe:recipe-list')


def create_recipe(user, **params):
    """Helper function to create a recipe"""
    defaults = {
        'title': 'Sample Recipe',
        'description': 'Sample Description',
        'time_minutes': 10,
        'price': Decimal('5.00'),
        'link': 'http://example.com/recipe.pdf',
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test the public features of the recipe API"""

    def setUp(self):
        """Set up the API client"""
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required to access the recipe API"""
        response = self.client.get(CREATE_RECIPE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeApiTests(TestCase):
    """Test the private features of the recipe API"""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'testpass123',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user, title='Another Recipe')

        response = self.client.get(CREATE_RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_recipe_list_limtted_to_user(self):
        """Test that recipes returned are for the authenticated user"""
        other_user = get_user_model().objects.create_user(
            'other@example.com',
            'testpass123',
        )
        create_recipe(user=other_user, title='Other User Recipe')
        create_recipe(user=self.user, title='User Recipe')
        response = self.client.get(CREATE_RECIPE_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
