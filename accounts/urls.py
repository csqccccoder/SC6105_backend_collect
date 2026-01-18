# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("me/", views.CurrentUserView.as_view(), name="current-user"),
    # 填你自己的
]
