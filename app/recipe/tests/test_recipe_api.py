"""Test for recipe API"""
import tempfile
import os
from PIL import Image
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

CREATE_RECIPE_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Create and return a recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def image_upload_url(recipe_id):
    """create and upload an image"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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


def create_user(**params):
    """create and return a new user"""
    return get_user_model().objects.create_user(**params)


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
        self.user = create_user(email='user@example.com', password='testpass123')
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
        other_user = create_user(
            email='other@example.com',
            password='testpass123'
        )
        create_recipe(user=other_user, title='Other User Recipe')
        create_recipe(user=self.user, title='User Recipe')
        response = self.client.get(CREATE_RECIPE_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_recipe_detail(self):
        """
        Test get recipe detail
        """
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe"""
        payload = {
            'title': "Sample recipe",
            'time_minutes': 30,
            'price': Decimal('5.99')
        }
        res = self.client.post(CREATE_RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update"""
        orginal_link = 'http://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample Recipe',
            link=orginal_link
        )
        payload = {'title': 'New Recipe Title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, orginal_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test for full update"""
        recipe = create_recipe(
            user=self.user,
            title='Sample Recipe',
            link='http://example.com/recipe.pdf',
            description='New Sample Description',
        )
        url = detail_url(recipe.id)
        payload = {
            'title': 'Updated Recipe',
            'link': 'http://example.com/updated_recipe.pdf',
            'description': 'Updated Description',
            'time_minutes': 20,
            'price': Decimal('9.99')
        }
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing recipe user results in error"""
        new_user = create_user(email="newuser@example.com", password='test123')
        recipe = create_recipe(user=self.user)
        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test delete recipe"""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_users_recipe_error(self):
        """
        Test trying to delete another users of recipe give error
        """
        new_user = create_user(email="newuser@example.com", password='test123')
        recipe = create_recipe(user=new_user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        # self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags"""
        payload = {
            'title': 'Thai Prawn Curry',
            'time_minutes': 30,
            'price': Decimal('5.99'),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}]
        }
        res = self.client.post(CREATE_RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        recipe = recipes[0]
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(name=tag['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tag(self):
        """
        Test creating a recipe with existing tag
        """
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal('4.50'),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}]
        }
        res = self.client.post(CREATE_RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(name=tag['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating tag when updating a recipe"""
        recipe = create_recipe(user=self.user)
        payload = {'tags': [{'name': 'Breakfast'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Breakfast')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe"""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        """Test clearing a recipe tags"""
        tag = Tag.objects.create(user=self.user,  name='Dessert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Test creating recipe with ingredient success"""
        payload = {
            'title': 'Thai Prawn Curry',
            'time_minutes': 30,
            'price': Decimal('5.99'),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}],
            'ingredients': [{'name': 'Prawns'}, {'name': 'Curry Paste'}]
        }
        res = self.client.post(CREATE_RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        recipe = recipes[0]
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipe.ingredients.count(), 2)
        for tag in payload['ingredients']:
            exists = recipe.ingredients.filter(name=tag['name'], user=self.user).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """Test creating a recipe with existing ingredient"""
        ingredient_rice = Ingredient.objects.create(user=self.user, name='Rice')
        payload = {
            'title': 'Fried Rice',
            'time_minutes': 20,
            'price': Decimal('3.50'),
            'ingredients': [{'name': 'Rice'}, {'name': 'Vegetables'}]
        }
        res = self.client.post(CREATE_RECIPE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient_rice, recipe.ingredients.all())

        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'], user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_update_recipe_with_new_ingredient(self):
        """Test updating a recipe with new ingredient"""
        recipe = create_recipe(user=self.user)
        payload = {'ingredients': [{'name': 'Chicken'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name='Chicken')
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe"""
        ingredient_chicken = Ingredient.objects.create(user=self.user, name='Chicken')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient_chicken)

        ingredient_vegetables = Ingredient.objects.create(user=self.user, name='Vegetables')
        payload = {'ingredients': [{'name': 'Vegetables'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient_vegetables, recipe.ingredients.all())
        self.assertNotIn(ingredient_chicken, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing a recipe ingredients"""
        ingredient1= Ingredient.objects.create(user=self.user, name='Salt')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Pepper')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1, ingredient2)
        payload = {'ingredients': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_by_tags(self):
        """Test filtering recipes by tags"""
        r1 = create_recipe(user=self.user, title='Thai vegetarian curry')
        r2 = create_recipe(user=self.user, title='Indian vegetarian curry')
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Vegetarian')
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_recipe(user=self.user, title = 'Fish and chips')
        params = {'tags': f'{tag1.id},{tag2.id}'}
        res = self.client.get(CREATE_RECIPE_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        """Test filtering recipes by ingredients"""
        r1 = create_recipe(user=self.user, title='Posh beans on toast')
        r2 = create_recipe(user=self.user, title='Chicken cacciatore')
        in1 = Ingredient.objects.create(user=self.user, name='Feta Cheese')
        in2 = Ingredient.objects.create(user=self.user, name='Chicken')
        r1.ingredients.add(in1)
        r2.ingredients.add(in2)
        r3 = create_recipe(user=self.user, title = 'Red Lentil Daal')

        params = {'ingredients': f'{in1.id},{in2.id}'}
        res = self.client.get(CREATE_RECIPE_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)



class ImageUploadTests(TestCase):
    """Tests for the image upload API"""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'password123',
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self) -> None:
        self.recipe.image.delete()

    def test_upload_image(self):
        """test uploading an image to a recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_file:
            img = Image.new('RGB', (10, 10))
            img.save(temp_file, format='JPEG')
            temp_file.seek(0)
            payload = {'image': temp_file}
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image"""
        url = image_upload_url(self.recipe.id)
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)