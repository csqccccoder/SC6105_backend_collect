from rest_framework import permissions
from .models import User


class IsAdmin(permissions.BasePermission):
    """
    只允许管理员访问
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == User.Role.ADMIN
        )


class IsManager(permissions.BasePermission):
    """
    只允许经理访问
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == User.Role.MANAGER
        )


class IsSupportStaff(permissions.BasePermission):
    """
    只允许支持人员访问
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == User.Role.SUPPORT_STAFF
        )


class IsAdminOrManager(permissions.BasePermission):
    """
    只允许管理员或经理访问
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in [User.Role.ADMIN, User.Role.MANAGER]
        )


class IsStaffMember(permissions.BasePermission):
    """
    只允许员工（管理员、经理或支持人员）访问
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in [User.Role.ADMIN, User.Role.MANAGER, User.Role.SUPPORT_STAFF]
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    只允许对象所有者或管理员访问
    """
    def has_object_permission(self, request, view, obj):
        # 管理员可以访问任何对象
        if request.user.role == User.Role.ADMIN:
            return True
        
        # 对象所有者可以访问自己的对象
        # 假设对象有 user 或 created_by 字段
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class ReadOnlyOrAdmin(permissions.BasePermission):
    """
    只读权限给所有认证用户，写权限只给管理员
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # 读取操作允许所有认证用户
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 写操作只允许管理员
        return request.user.role == User.Role.ADMIN
