from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, 
    LoginView, 
    LogoutView, 
    RefreshTokenView, 
    RoleView,
    CurrentUserView,
    TeamViewSet,
    AuditLogViewSet
)

# 创建路由器并注册ViewSet
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')

app_name = 'accounts'

urlpatterns = [
    # 认证相关路由
    path('auth/sso', LoginView.as_view(), name='login'),
    path('auth/logout', LogoutView.as_view(), name='logout'),
    path('auth/refresh', RefreshTokenView.as_view(), name='refresh'),
    path('auth/me', CurrentUserView.as_view(), name='current-user'),  # 符合API文档
    
    # 角色列表
    path('roles', RoleView.as_view(), name='roles'),
    
    # 用户、团队、审计日志相关路由（由router自动生成）
    # GET    /users/          - 用户列表
    # POST   /users/          - 创建用户
    # GET    /users/{id}/     - 用户详情
    # PUT    /users/{id}/     - 更新用户
    # PATCH  /users/{id}/     - 部分更新用户
    # DELETE /users/{id}/     - 删除用户
    # GET    /users/me/       - 当前用户信息（备用路径）
    # POST   /users/{id}/change-role/    - 修改用户角色
    # POST   /users/{id}/toggle-active/  - 切换用户激活状态
    path('', include(router.urls)),
]
