# kb/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("articles/", views.KnowledgeArticleListCreateView.as_view(), name="kb-articles"),
    path("articles/<int:pk>/", views.KnowledgeArticleDetailView.as_view(), name="kb-article-detail"),
    path("search/", views.KnowledgeSearchView.as_view(), name="kb-search"),
]