from rest_framework import serializers
from .models import KnowledgeArticle, Tag


class TagSerializer(serializers.ModelSerializer):
    """Tag serializer"""
    class Meta:
        model = Tag
        fields = ['name']


class KnowledgeArticleSerializer(serializers.ModelSerializer):
    """
    Knowledge Article Serializer
    Outputs camelCase fields as required by frontend
    """
    # Read-only fields with camelCase names
    id = serializers.IntegerField(read_only=True)
    authorId = serializers.IntegerField(source='created_by.id', read_only=True, allow_null=True)
    authorName = serializers.SerializerMethodField()
    viewCount = serializers.IntegerField(source='view_count', read_only=True)
    helpfulCount = serializers.IntegerField(source='helpful_count', read_only=True)
    notHelpfulCount = serializers.IntegerField(source='not_helpful_count', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    publishedAt = serializers.DateTimeField(source='published_at', read_only=True, allow_null=True)
    
    # Tags as array of strings
    tags = serializers.SerializerMethodField()
    
    # Writable fields
    title = serializers.CharField(max_length=255)
    content = serializers.CharField()
    summary = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    category = serializers.CharField(max_length=100)
    status = serializers.ChoiceField(
        choices=['draft', 'published', 'archived'],
        default='draft',
        read_only=True
    )
    accessLevel = serializers.ChoiceField(
        source='access_level',
        choices=['public', 'internal'],
        default='public'
    )
    isFAQ = serializers.BooleanField(source='is_faq', default=False)
    
    class Meta:
        model = KnowledgeArticle
        fields = [
            'id', 'title', 'content', 'summary', 'category', 'tags',
            'status', 'accessLevel', 'isFAQ',
            'authorId', 'authorName',
            'viewCount', 'helpfulCount', 'notHelpfulCount',
            'createdAt', 'updatedAt', 'publishedAt'
        ]
    
    def get_authorName(self, obj):
        """Get author name"""
        if obj.created_by:
            # Try to get full name, fallback to username
            full_name = f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
            return full_name if full_name else obj.created_by.username
        return None
    
    def get_tags(self, obj):
        """Return tags as array of strings"""
        return [tag.name for tag in obj.tags.all()]
    
    def create(self, validated_data):
        """Create article with tags"""
        # Extract tags if provided in context
        tags_data = self.context.get('tags', [])
        
        # Create article
        article = KnowledgeArticle.objects.create(**validated_data)
        
        # Add tags
        if tags_data:
            self._update_tags(article, tags_data)
        
        return article
    
    def update(self, instance, validated_data):
        """Update article with tags"""
        # Extract tags if provided in context
        tags_data = self.context.get('tags', None)
        
        # Update article fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update tags if provided
        if tags_data is not None:
            self._update_tags(instance, tags_data)
        
        return instance
    
    def _update_tags(self, article, tags_data):
        """Update article tags"""
        article.tags.clear()
        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(name=tag_name.strip())
            article.tags.add(tag)


class KnowledgeArticleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    id = serializers.IntegerField(read_only=True)
    authorId = serializers.IntegerField(source='created_by.id', read_only=True, allow_null=True)
    authorName = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    viewCount = serializers.IntegerField(source='view_count', read_only=True)
    helpfulCount = serializers.IntegerField(source='helpful_count', read_only=True)
    notHelpfulCount = serializers.IntegerField(source='not_helpful_count', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    publishedAt = serializers.DateTimeField(source='published_at', read_only=True, allow_null=True)
    accessLevel = serializers.CharField(source='access_level', read_only=True)
    isFAQ = serializers.BooleanField(source='is_faq', read_only=True)
    
    class Meta:
        model = KnowledgeArticle
        fields = [
            'id', 'title', 'summary', 'category', 'tags',
            'status', 'accessLevel', 'isFAQ',
            'authorId', 'authorName',
            'viewCount', 'helpfulCount', 'notHelpfulCount',
            'createdAt', 'updatedAt', 'publishedAt'
        ]
    
    def get_authorName(self, obj):
        """Get author name"""
        if obj.created_by:
            full_name = f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
            return full_name if full_name else obj.created_by.username
        return None
    
    def get_tags(self, obj):
        """Return tags as array of strings"""
        return [tag.name for tag in obj.tags.all()]


class FeedbackSerializer(serializers.Serializer):
    """Feedback serializer"""
    helpful = serializers.BooleanField()
