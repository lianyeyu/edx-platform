"""
Classes that override default django-oauth-toolkit behavior
"""

from django.contrib.auth import authenticate as django_authenticate, get_user_model
from oauth2_provider.oauth2_validators import OAuth2Validator


def authenticate(username, password):
    """
    Authenticate the user, allowing the user to identify themself either by
    username or email
    """

    if '@' in username:
        UserModel = get_user_model()  # pylint: disable=invalid-name
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None
        else:
            username = user.username
    return django_authenticate(username=username, password=password)


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
