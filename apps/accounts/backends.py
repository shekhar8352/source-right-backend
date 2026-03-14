from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOrUsernameBackend(ModelBackend):
    """
    Authenticate by username (case-insensitive) or by email.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None and "email" in kwargs:
            username = kwargs.get("email")
        if username is None or password is None:
            return None

        # Try username (case-insensitive) first, then email
        user = (
            UserModel.objects.filter(username__iexact=username).first()
            or UserModel.objects.filter(email__iexact=username).first()
        )
        if user is None:
            UserModel().set_password(password)  # timing attack mitigation
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
