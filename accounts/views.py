# accounts/views.py 填自己的逻辑
from rest_framework.views import APIView
from rest_framework.response import Response

class LoginView(APIView):
    """
    Example placeholder for login.
    Later: integrate real SSO / token logic.
    """
    def post(self, request, *args, **kwargs):
        # TODO: replace with real login
        return Response({"message": "login placeholder"})

class CurrentUserView(APIView):
    """
    Example placeholder for fetching current user info.
    """
    def get(self, request, *args, **kwargs):
        # TODO: return current user info
        return Response({"username": "demo-user"})