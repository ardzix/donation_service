from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import User


class SSOAuthentication(JWTAuthentication):
    def authenticate(self, request):
        """
        Authenticate user based on sso_user_id from token.
        """
        header = self.get_header(request)
        if header is None:
            return None
        
        raw_token = self.get_raw_token(header)
        if not raw_token:
            return None

        validated_token = self.get_validated_token(raw_token)
        # print(validated_token)
        sso_user_id = validated_token.get("user_id")

        if not sso_user_id:
            raise AuthenticationFailed("Invalid token: 'user_id' not found.")

        # Get or create user based on sso_user_id
        user, created = User.objects.get_or_create(username=sso_user_id, defaults={
            "email": "",  # Optional: you can update later if needed
        })

        return user, validated_token
