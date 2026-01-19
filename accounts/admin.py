from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Team, TeamMembership, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'name', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'date_joined']
    search_fields = ['email', 'name', 'username']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('name', 'avatar_url', 'username', 'department', 'phone')}),
        (_('Permissions'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'updated_at')}),
    )

    readonly_fields = ['date_joined', 'last_login', 'updated_at']

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'name', 'role'),
        }),
    )


class TeamMembershipInline(admin.TabularInline):
    """Team membership inline admin"""
    model = TeamMembership
    extra = 1
    fields = ['user', 'role', 'joined_at']
    readonly_fields = ['joined_at']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Team admin"""
    list_display = ['name', 'leader', 'get_member_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [TeamMembershipInline]
    
    fieldsets = (
        (None, {'fields': ('name', 'description', 'leader')}),
        (_('Timestamps'), {'fields': ('created_at', 'updated_at')}),
    )
    
    def get_member_count(self, obj):
        return obj.member_count
    get_member_count.short_description = 'Members'


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    """Team membership admin"""
    list_display = ['team', 'user', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['team__name', 'user__email', 'user__name']
    ordering = ['-joined_at']
    readonly_fields = ['joined_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Audit log admin"""
    list_display = ['user_email', 'action', 'ip_address', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['user_email', 'action', 'details']
    ordering = ['-timestamp']
    readonly_fields = ['user', 'user_email', 'action', 'details', 'ip_address', 'timestamp']
    
    def has_add_permission(self, request):
        """禁止手动添加审计日志"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """禁止删除审计日志"""
        return False
