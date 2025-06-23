"""
Serializers for user-related data.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object."""

    class Meta:
        model = get_user_model()
        fields = ('email', 'name', 'password')
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 5,
            }
        }

    def create(self, validated_data):
        """Create and return a new user."""
        user = get_user_model().objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        """Update and return an existing user."""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)

        user.save()
        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for user authentication token."""
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        """Validate and authenticate the user."""
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError(_('Must include "email" and "password".'))

        user = authenticate(request=self.context.get('request'), username=email, password=password)

        if user is None:
            raise serializers.ValidationError(_('Unable to log in with provided credentials.'), code='authentication')

        attrs['user'] = user
        return attrs
