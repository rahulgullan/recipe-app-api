"""
Test for admin functionality in the core app.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client


class AdminSiteTests(TestCase):
    """
    Test for the Django admin site functionality.
    """

    def setUp(self):
        """Create user and client for testing."""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="testpass123"
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            name='Test User',
        )
    def test_users_listed(self):
        """
        Test that users are listed on the admin page.
        """
        url = reverse('admin:core_user_changelist')
        response = self.client.get(url)

        self.assertContains(response, self.user.email)
        self.assertContains(response, self.user.name)

    def test_edit_user_page(self):
        """
        Test that the edit user page works.
        """
        url = reverse('admin:core_user_change', args=[self.user.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.email)
        # self.assertContains(response, self.user.name)

    def test_create_user_page(self):
        """Create user page"""
        url = reverse('admin:core_user_add')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)