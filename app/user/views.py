"""
Views for user-related operations.
"""

from rest_framework import generics, permissions, authentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from user.serializers import UserSerializer, AuthTokenSerializer

class CreateUserView(generics.CreateAPIView):
    """
    View to create a new user.
    """
    serializer_class = UserSerializer
    permission_classes = []  # Allow any user to access this view
    authentication_classes = []  # No authentication required for user creation

    def perform_create(self, serializer):
        """
        Save the new user instance.
        """
        serializer.save()  # Calls the create method in UserSerializer


class CreateTokenView(ObtainAuthToken):
    """
    View to create an authentication token for a user.
    """
    serializer_class = AuthTokenSerializer  # Use the same serializer for token creation
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES  # Use default renderer classes

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to create a token.
        """
        return super().post(request, *args, **kwargs)  # Call the parent method to handle token creation


class ManageUserView(generics.RetrieveUpdateAPIView):
    """
    View to manage the authenticated user's profile.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]  # Only authenticated users can access this view
    authentication_classes = [authentication.TokenAuthentication]  # Use token authentication

    def get_object(self):
        """
        Return the authenticated user instance.
        """
        return self.request.user  # Return the user associated with the request