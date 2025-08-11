"""
Test for tags API
"""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import Tag, Recipe
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def create_user(email='user@example.com', password='testpass123'):
    """Helper function to create a user."""
    return get_user_model().objects.create_user(email=email, password=password)


def detail_url(tag_id):
    """create and return tag url"""
    return reverse('recipe:tag-detail', args=[tag_id])


class PublicTagsApiTests(TestCase):
    """Test the public features of the tags API."""

    def setUp(self):
        """Set up the API client."""
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required to access the tags API."""
        response = self.client.get(TAGS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test the private features of the tags API."""

    def setUp(self) -> None:
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags."""
        Tag.objects.create(user=self.user, name="Vegan")
        Tag.objects.create(user=self.user, name="Dessert")
        response = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_tags_limitted_to_user(self):
        """Test list of tags is limited to authenticated user."""
        user2 = create_user(email="user2@example.com", password="testpass123")
        Tag.objects.create(user=user2, name="Fruity")
        tag = Tag.objects.create(user=self.user, name="Comfort Food")
        response = self.client.get(TAGS_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], tag.name)
        self.assertEqual(response.data[0]['id'], tag.id)

    def test_update_tag(self):
        """Test update a tag"""
        tag = Tag.objects.create(user=self.user, name="After Dinner")
        payload = {'name': 'Dessert'}
        url = detail_url(tag.id)
        response = self.client.patch(url, payload)
        tag.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tags(self):
        """Test deleting a tag"""
        tag = Tag.objects.create(user=self.user, name="Lunch")
        url = detail_url(tag.id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())

    def test_filter_tags_assigned_to_recipes(self):
        """Test listing tags assigned to recipes"""
        tag1 = Tag.objects.create(user=self.user, name="Breakfast")
        tag2 = Tag.objects.create(user=self.user, name="Lunch")
        recipe = Recipe.objects.create(
            title='Green Eggs on Toast',
            time_minutes=10,
            price=Decimal('2.50'),
            user=self.user
        )
        recipe.tags.add(tag1)
        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_tags_assigned_to_recipes_unique(self):
        """Test filtering tags assigned to recipes returns unique results"""
        tag1 = Tag.objects.create(user=self.user, name="Breakfast")
        Tag.objects.create(user=self.user, name="Lunch")
        recipe1 = Recipe.objects.create(
            title='Green Eggs on Toast',
            time_minutes=10,
            price=Decimal('2.50'),
            user=self.user
        )
        recipe1.tags.add(tag1)
        recipe2 = Recipe.objects.create(
            title='Avocado Toast',
            time_minutes=5,
            price=Decimal('3.00'),
            user=self.user
        )
        recipe2.tags.add(tag1)
        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)