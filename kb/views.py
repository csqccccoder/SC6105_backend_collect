from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from django.utils import timezone
from django.core.paginator import Paginator
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import KnowledgeArticle, Tag
from .serializers import (
    KnowledgeArticleSerializer,
    KnowledgeArticleListSerializer,
    FeedbackSerializer,
    PaginatedKnowledgeArticleListResponseSerializer,
    MessageResponseSerializer,
    DeleteResponseSerializer
)


def is_staff_user(user):
    """
    Check if user is staff/manager/admin
    SSO-compatible: Prioritizes 'role' field from SSO system
    Fallback: Django's built-in is_staff/is_superuser
    """
    # 1. Priority check: SSO synced role field
    if hasattr(user, 'role') and user.role:
        # Ensure role is string and in allowed roles list
        if isinstance(user.role, str) and user.role.lower() in ['support_staff', 'staff', 'manager', 'admin']:
            return True
    
    # 2. Fallback to Django built-in permission fields
    return user.is_staff or user.is_superuser


def get_visible_articles_queryset(user):
    """Get articles visible to the current user"""
    base_queryset = KnowledgeArticle.objects.filter(deleted_at__isnull=True)
    
    if is_staff_user(user):
        # Staff can see all articles
        return base_queryset
    else:
        # End users can only see published public articles
        return base_queryset.filter(
            status='published',
            access_level='public'
        )


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(name='keyword', type=OpenApiTypes.STR, required=False, description='Search keyword'),
            OpenApiParameter(name='query', type=OpenApiTypes.STR, required=False, description='Search query'),
            OpenApiParameter(name='category', type=OpenApiTypes.STR, required=False, description='Filter by category'),
            OpenApiParameter(name='tag', type=OpenApiTypes.STR, required=False, description='Filter by tag'),
            OpenApiParameter(name='status', type=OpenApiTypes.STR, required=False, description='Filter by status'),
            OpenApiParameter(name='page', type=OpenApiTypes.INT, required=False, description='Page number'),
            OpenApiParameter(name='pageSize', type=OpenApiTypes.INT, required=False, description='Page size'),
        ],
        responses={200: PaginatedKnowledgeArticleListResponseSerializer},
        operation_id='kb_articles_list',
        summary='List knowledge base articles'
    ),
    list_all=extend_schema(
        parameters=[
            OpenApiParameter(name='keyword', type=OpenApiTypes.STR, required=False, description='Search keyword'),
            OpenApiParameter(name='query', type=OpenApiTypes.STR, required=False, description='Search query'),
            OpenApiParameter(name='category', type=OpenApiTypes.STR, required=False, description='Filter by category'),
            OpenApiParameter(name='tag', type=OpenApiTypes.STR, required=False, description='Filter by tag'),
            OpenApiParameter(name='status', type=OpenApiTypes.STR, required=False, description='Filter by status'),
            OpenApiParameter(name='page', type=OpenApiTypes.INT, required=False, description='Page number'),
            OpenApiParameter(name='pageSize', type=OpenApiTypes.INT, required=False, description='Page size'),
        ],
        responses={200: PaginatedKnowledgeArticleListResponseSerializer},
        operation_id='kb_articles_list_all',
        summary='List all articles (staff only)'
    ),
    retrieve=extend_schema(
        responses={200: KnowledgeArticleSerializer},
        operation_id='kb_articles_retrieve',
        summary='Retrieve article details'
    ),
    create=extend_schema(
        request=KnowledgeArticleSerializer,
        responses={201: KnowledgeArticleSerializer},
        operation_id='kb_articles_create',
        summary='Create article (staff only)'
    ),
    update=extend_schema(
        request=KnowledgeArticleSerializer,
        responses={200: KnowledgeArticleSerializer},
        operation_id='kb_articles_update',
        summary='Update article (staff only)'
    ),
    destroy=extend_schema(
        responses={200: DeleteResponseSerializer},
        operation_id='kb_articles_destroy',
        summary='Delete article (staff only)'
    ),
    publish=extend_schema(
        responses={200: KnowledgeArticleSerializer},
        operation_id='kb_articles_publish',
        summary='Publish article (staff only)'
    ),
    archive=extend_schema(
        responses={200: KnowledgeArticleSerializer},
        operation_id='kb_articles_archive',
        summary='Archive article (staff only)'
    )
)
class KnowledgeArticleViewSet(ViewSet):
    """Knowledge Article ViewSet"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """
        GET /api/knowledge/articles
        List articles with filters and pagination (visible to current user)
        """
        # Get visible articles
        queryset = get_visible_articles_queryset(request.user)
        
        # Apply filters
        keyword = request.query_params.get('keyword', None)
        query = request.query_params.get('query', None)
        category = request.query_params.get('category', None)
        tag = request.query_params.get('tag', None)
        status_filter = request.query_params.get('status', None)
        
        # Keyword or query search
        search_term = keyword or query
        if search_term:
            queryset = queryset.filter(
                Q(title__icontains=search_term) |
                Q(content__icontains=search_term) |
                Q(summary__icontains=search_term)
            )
        
        # Category filter (exact match)
        if category:
            queryset = queryset.filter(category=category)
        
        # Tag filter
        if tag:
            queryset = queryset.filter(tags__name=tag)
        
        # Status filter (only for staff)
        if status_filter and is_staff_user(request.user):
            queryset = queryset.filter(status=status_filter)
        
        # Order by created_at desc
        queryset = queryset.order_by('-created_at').distinct()
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('pageSize', 10))
        
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize
        serializer = KnowledgeArticleListSerializer(page_obj.object_list, many=True)
        
        # Return paginated response
        return Response({
            'items': serializer.data,
            'page': page,
            'pageSize': page_size,
            'total': paginator.count,
            'totalPages': paginator.num_pages
        })
    
    def list_all(self, request):
        """
        GET /api/knowledge/articles/all
        List all articles (staff only)
        """
        if not is_staff_user(request.user):
            return Response(
                {'detail': 'Permission denied. Staff access required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all articles (including drafts, internal, archived)
        queryset = KnowledgeArticle.objects.filter(deleted_at__isnull=True)
        
        # Apply filters (same as list)
        keyword = request.query_params.get('keyword', None)
        query = request.query_params.get('query', None)
        category = request.query_params.get('category', None)
        tag = request.query_params.get('tag', None)
        status_filter = request.query_params.get('status', None)
        
        search_term = keyword or query
        if search_term:
            queryset = queryset.filter(
                Q(title__icontains=search_term) |
                Q(content__icontains=search_term) |
                Q(summary__icontains=search_term)
            )
        
        if category:
            queryset = queryset.filter(category=category)
        
        if tag:
            queryset = queryset.filter(tags__name=tag)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        queryset = queryset.order_by('-created_at').distinct()
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('pageSize', 10))
        
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = KnowledgeArticleListSerializer(page_obj.object_list, many=True)
        
        return Response({
            'items': serializer.data,
            'page': page,
            'pageSize': page_size,
            'total': paginator.count,
            'totalPages': paginator.num_pages
        })
    
    def retrieve(self, request, pk=None):
        """
        GET /api/knowledge/articles/:id
        Get article detail and increment view count
        """
        try:
            article = KnowledgeArticle.objects.get(pk=pk, deleted_at__isnull=True)
        except KnowledgeArticle.DoesNotExist:
            return Response(
                {'detail': 'Article not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check visibility
        if not is_staff_user(request.user):
            if article.status != 'published' or article.access_level != 'public':
                return Response(
                    {'detail': 'Article not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Increment view count
        article.increment_view_count()
        
        serializer = KnowledgeArticleSerializer(article)
        return Response(serializer.data)
    
    def create(self, request):
        """
        POST /api/knowledge/articles
        Create new article (staff only)
        """
        if not is_staff_user(request.user):
            return Response(
                {'detail': 'Permission denied. Staff access required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Extract tags from request data
        tags_data = request.data.get('tags', [])
        
        # Create serializer with context
        serializer = KnowledgeArticleSerializer(
            data=request.data,
            context={'tags': tags_data}
        )
        
        if serializer.is_valid():
            article = serializer.save(
                created_by=request.user,
                updated_by=request.user,
                status='draft',  # Default to draft
                published_at=None,
                view_count=0,
                helpful_count=0,
                not_helpful_count=0
            )
            
            # Return created article
            response_serializer = KnowledgeArticleSerializer(article)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """
        PUT /api/knowledge/articles/:id
        Update article (staff only)
        """
        if not is_staff_user(request.user):
            return Response(
                {'detail': 'Permission denied. Staff access required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            article = KnowledgeArticle.objects.get(pk=pk, deleted_at__isnull=True)
        except KnowledgeArticle.DoesNotExist:
            return Response(
                {'detail': 'Article not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Extract tags from request data
        tags_data = request.data.get('tags', None)
        
        serializer = KnowledgeArticleSerializer(
            article,
            data=request.data,
            partial=True,
            context={'tags': tags_data}
        )
        
        if serializer.is_valid():
            article = serializer.save(updated_by=request.user)
            response_serializer = KnowledgeArticleSerializer(article)
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """
        DELETE /api/knowledge/articles/:id
        Soft delete article (staff only)
        """
        if not is_staff_user(request.user):
            return Response(
                {'detail': 'Permission denied. Staff access required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            article = KnowledgeArticle.objects.get(pk=pk, deleted_at__isnull=True)
        except KnowledgeArticle.DoesNotExist:
            return Response(
                {'detail': 'Article not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Soft delete
        article.soft_delete()
        
        return Response({'deleted': True}, status=status.HTTP_200_OK)
    
    def publish(self, request, pk=None):
        """
        POST /api/knowledge/articles/:id/publish
        Publish article (staff only)
        """
        if not is_staff_user(request.user):
            return Response(
                {'detail': 'Permission denied. Staff access required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            article = KnowledgeArticle.objects.get(pk=pk, deleted_at__isnull=True)
        except KnowledgeArticle.DoesNotExist:
            return Response(
                {'detail': 'Article not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        article.publish()
        article.updated_by = request.user
        article.save()
        
        serializer = KnowledgeArticleSerializer(article)
        return Response(serializer.data)
    
    def archive(self, request, pk=None):
        """
        POST /api/knowledge/articles/:id/archive
        Archive article (staff only)
        """
        if not is_staff_user(request.user):
            return Response(
                {'detail': 'Permission denied. Staff access required.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            article = KnowledgeArticle.objects.get(pk=pk, deleted_at__isnull=True)
        except KnowledgeArticle.DoesNotExist:
            return Response(
                {'detail': 'Article not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        article.archive()
        article.updated_by = request.user
        article.save()
        
        serializer = KnowledgeArticleSerializer(article)
        return Response(serializer.data)
    
    @extend_schema(
        request=FeedbackSerializer,
        responses={200: MessageResponseSerializer},
        operation_id='kb_articles_feedback',
        summary='Submit article feedback'
    )
    def feedback(self, request, pk=None):
        """
        POST /api/knowledge/articles/:id/feedback
        Submit feedback (all authenticated users)
        """
        try:
            article = KnowledgeArticle.objects.get(pk=pk, deleted_at__isnull=True)
        except KnowledgeArticle.DoesNotExist:
            return Response(
                {'detail': 'Article not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check visibility for end users
        if not is_staff_user(request.user):
            if article.status != 'published' or article.access_level != 'public':
                return Response(
                    {'detail': 'Article not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            helpful = serializer.validated_data['helpful']
            article.add_feedback(helpful)
            
            return Response({'message': 'Feedback submitted successfully.'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    responses={200: KnowledgeArticleListSerializer(many=True)},
    operation_id='kb_faq_list',
    summary='List FAQ articles'
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def faq_list(request):
    """
    GET /api/knowledge/faq
    Get FAQ articles (visible to current user)
    """
    queryset = get_visible_articles_queryset(request.user).filter(is_faq=True)
    queryset = queryset.order_by('-created_at')
    
    serializer = KnowledgeArticleListSerializer(queryset, many=True)
    return Response(serializer.data)


@extend_schema(
    parameters=[
        OpenApiParameter(name='query', type=OpenApiTypes.STR, required=False, description='Search query'),
        OpenApiParameter(name='limit', type=OpenApiTypes.INT, required=False, description='Result limit'),
    ],
    responses={200: KnowledgeArticleListSerializer(many=True)},
    operation_id='kb_suggestions',
    summary='Get article search suggestions'
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def suggestions(request):
    """
    GET /api/knowledge/suggestions?query=xxx&limit=5
    Get article suggestions based on query (visible to current user)
    """
    query = request.query_params.get('query', '')
    limit = int(request.query_params.get('limit', 5))
    
    if not query:
        return Response([])
    
    queryset = get_visible_articles_queryset(request.user)
    queryset = queryset.filter(
        Q(title__icontains=query) |
        Q(content__icontains=query) |
        Q(summary__icontains=query)
    ).order_by('-view_count', '-created_at')[:limit]
    
    serializer = KnowledgeArticleListSerializer(queryset, many=True)
    return Response(serializer.data)


@extend_schema(
    responses={200: {'type': 'array', 'items': {'type': 'string'}}},
    operation_id='kb_categories_list',
    summary='List all categories'
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def categories_list(request):
    """
    GET /api/knowledge/categories
    Get all categories from visible articles
    """
    queryset = get_visible_articles_queryset(request.user)
    categories = queryset.values_list('category', flat=True).distinct().order_by('category')
    
    # Filter out empty categories
    categories = [cat for cat in categories if cat]
    
    return Response(categories)


@extend_schema(
    responses={200: {'type': 'array', 'items': {'type': 'string'}}},
    operation_id='kb_tags_list',
    summary='List all tags'
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tags_list(request):
    """
    GET /api/knowledge/tags
    Get all tags from visible articles
    """
    queryset = get_visible_articles_queryset(request.user)
    
    # Get all tags from visible articles using correct related_name 'articles'
    tags = Tag.objects.filter(articles__in=queryset).distinct().order_by('name')
    
    return Response(list(tags.values_list('name', flat=True)))
