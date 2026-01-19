from django.db import models
from django.conf import settings
from django.utils import timezone


class Tag(models.Model):
    """Tag model for knowledge articles"""
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'kb_tag'
        ordering = ['name']

    def __str__(self):
        return self.name


class KnowledgeArticle(models.Model):
    """Knowledge Base Article Model - SQLite Compatible"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    ACCESS_LEVEL_CHOICES = [
        ('public', 'Public'),
        ('internal', 'Internal'),
    ]
    
    # Basic fields
    title = models.CharField(max_length=255)
    content = models.TextField(help_text='Markdown content')
    summary = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100)
    
    # Many-to-many relationship with tags (SQLite compatible)
    tags = models.ManyToManyField(Tag, related_name='articles', blank=True)
    
    # Status and access
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft'
    )
    access_level = models.CharField(
        max_length=20, 
        choices=ACCESS_LEVEL_CHOICES, 
        default='public'
    )
    is_faq = models.BooleanField(default=False)
    
    # User relationships
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_articles'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_articles'
    )
    
    # Metrics
    view_count = models.IntegerField(default=0)
    helpful_count = models.IntegerField(default=0)
    not_helpful_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'kb_knowledge_article'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'access_level']),
            models.Index(fields=['category']),
            models.Index(fields=['is_faq']),
            models.Index(fields=['deleted_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def soft_delete(self):
        """Soft delete the article"""
        self.deleted_at = timezone.now()
        self.save()
    
    def publish(self):
        """Publish the article"""
        self.status = 'published'
        if not self.published_at:
            self.published_at = timezone.now()
        self.save()
    
    def archive(self):
        """Archive the article"""
        self.status = 'archived'
        self.save()
    
    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def add_feedback(self, helpful):
        """Add feedback"""
        if helpful:
            self.helpful_count += 1
        else:
            self.not_helpful_count += 1
        self.save(update_fields=['helpful_count', 'not_helpful_count'])
