from django.contrib import admin
from .models import KnowledgeArticle, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Tag admin"""
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(KnowledgeArticle)
class KnowledgeArticleAdmin(admin.ModelAdmin):
    """Knowledge Article admin"""
    list_display = [
        'id', 'title', 'category', 'status', 'access_level', 
        'is_faq', 'view_count', 'created_by', 'created_at'
    ]
    list_filter = ['status', 'access_level', 'is_faq', 'category', 'created_at']
    search_fields = ['title', 'content', 'summary']
    readonly_fields = [
        'view_count', 'helpful_count', 'not_helpful_count',
        'created_at', 'updated_at', 'published_at', 'deleted_at'
    ]
    filter_horizontal = ['tags']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'summary', 'content', 'category', 'tags')
        }),
        ('Status & Access', {
            'fields': ('status', 'access_level', 'is_faq')
        }),
        ('Metrics', {
            'fields': ('view_count', 'helpful_count', 'not_helpful_count')
        }),
        ('User Information', {
            'fields': ('created_by', 'updated_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at', 'deleted_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by and updated_by"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    actions = ['publish_articles', 'archive_articles', 'soft_delete_articles']
    
    def publish_articles(self, request, queryset):
        """Bulk publish articles"""
        for article in queryset:
            article.publish()
        self.message_user(request, f'{queryset.count()} articles published.')
    publish_articles.short_description = 'Publish selected articles'
    
    def archive_articles(self, request, queryset):
        """Bulk archive articles"""
        for article in queryset:
            article.archive()
        self.message_user(request, f'{queryset.count()} articles archived.')
    archive_articles.short_description = 'Archive selected articles'
    
    def soft_delete_articles(self, request, queryset):
        """Bulk soft delete articles"""
        for article in queryset:
            article.soft_delete()
        self.message_user(request, f'{queryset.count()} articles deleted.')
    soft_delete_articles.short_description = 'Soft delete selected articles'
