"""
Classes that override default django-oauth-toolkit behavior
"""

from django.contrib.auth import authenticate
from oauth2_provider.oauth2_validators import OAuth2Validator

class EdxOAuth2Validator(OAuth2Validator):
    """
    Validator class that mimics the default behavior, but does not require
    users to be validated.
    """

    def validate_user(self, username, password, client, request, *args, **kwargs):
        """
        Authenticate users, but allow inactive users (with u.is_active == False)
        to authenticate.
        """
        user = authenticate(username=username, password=password)
        if user is not None:
            request.user = user
            return True
        return False
