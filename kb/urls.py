from django.urls import path
from .views import (
    KnowledgeArticleViewSet,
    faq_list,
    suggestions,
    categories_list,
    tags_list
)

app_name = 'kb'

# Initialize viewset
article_viewset = KnowledgeArticleViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

article_detail_viewset = KnowledgeArticleViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'delete': 'destroy'
})

article_all_viewset = KnowledgeArticleViewSet.as_view({
    'get': 'list_all'
})

article_publish_viewset = KnowledgeArticleViewSet.as_view({
    'post': 'publish'
})

article_archive_viewset = KnowledgeArticleViewSet.as_view({
    'post': 'archive'
})

article_feedback_viewset = KnowledgeArticleViewSet.as_view({
    'post': 'feedback'
})

urlpatterns = [
    # Article CRUD
    path('articles/', article_viewset, name='article-list'),
    path('articles/all/', article_all_viewset, name='article-list-all'),
    path('articles/<int:pk>/', article_detail_viewset, name='article-detail'),
    
    # Article actions
    path('articles/<int:pk>/publish/', article_publish_viewset, name='article-publish'),
    path('articles/<int:pk>/archive/', article_archive_viewset, name='article-archive'),
    path('articles/<int:pk>/feedback/', article_feedback_viewset, name='article-feedback'),
    
    # Other endpoints
    path('faq/', faq_list, name='faq-list'),
    path('suggestions/', suggestions, name='suggestions'),
    path('categories/', categories_list, name='categories-list'),
    path('tags/', tags_list, name='tags-list'),
]
