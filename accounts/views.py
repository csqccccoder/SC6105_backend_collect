import os
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from google.oauth2 import id_token
from google.auth.transport import requests
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import User, Team, TeamMembership, AuditLog, Notification, NotificationPreference
from .permissions import IsAdmin, IsStaffMember, IsAdminOrManager
from .serializers import (
    UserSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    CurrentUserSerializer,
    TeamSerializer,
    TeamCreateSerializer,
    TeamUpdateSerializer,
    AddTeamMemberSerializer,
    AuditLogSerializer,
    RoleItemSerializer,
    LoginRequestSerializer,
    LoginResponseDataSerializer,
    LogoutRequestSerializer,
    RefreshTokenRequestSerializer,
    ChangeRoleRequestSerializer,
    NotificationSerializer,
    NotificationPreferenceSerializer,
)
from .response_wrapper import APIResponse, success_response, error_response
from .pagination import CustomPagination


# ===== 辅助函数 =====

def get_client_ip(request):
    """获取客户端 IP 地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def create_audit_log(user, action, details=None, request=None):
    """创建审计日志"""
    ip_address = get_client_ip(request) if request else None
    AuditLog.objects.create(
        user=user,
        user_email=user.email,
        action=action,
        details=details or '',
        ip_address=ip_address
    )
    return True


class UserViewSet(viewsets.ModelViewSet):
    """
    用户视图集
    
    提供用户的CRUD操作
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get_serializer_class(self):
        """根据不同的action返回不同的序列化器"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer
    
    def get_permissions(self):
        """根据不同的action设置不同的权限"""
        # 只有管理员可以创建、更新、删除用户
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        elif self.action in ['list', 'retrieve', 'current_user']:
            return [IsAuthenticated()]
        return super().get_permissions()
    
    def list(self, request, *args, **kwargs):
        """
        获取用户列表（带分页）
        支持查询参数: page, pageSize, keyword, role
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # 关键词搜索
        keyword = request.query_params.get('keyword', None)
        if keyword:
            from django.db import models
            queryset = queryset.filter(
                models.Q(name__icontains=keyword) | 
                models.Q(email__icontains=keyword)
            )
        
        # 角色过滤
        role = request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return APIResponse(
                data=paginated_response.data,
                message='Success',
                code=200
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """创建用户"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # 使用 UserSerializer 返回完整的用户信息（包括 id）
        instance = serializer.instance
        response_serializer = UserSerializer(instance)
        
        return APIResponse(
            data=response_serializer.data,
            message='User created successfully',
            code=201,
            status_code=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        """获取单个用户详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """更新用户"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return success_response(serializer.data, message='User updated successfully')
    
    def destroy(self, request, *args, **kwargs):
        """删除用户"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return APIResponse(
            data=None,
            message='User deleted successfully',
            code=200
        )
    
    @extend_schema(
        responses={
            200: OpenApiResponse(response=CurrentUserSerializer)
        },
        tags=["Users"]
    )
    @action(detail=False, methods=['get'], url_path='me')
    def current_user(self, request):
        """
        获取当前登录用户信息
        GET /users/me
        """
        serializer = CurrentUserSerializer(request.user)
        return success_response(serializer.data)
    
    @extend_schema(
        request=ChangeRoleRequestSerializer,
        responses={
            200: OpenApiResponse(response=UserSerializer),
            400: OpenApiResponse(),
            403: OpenApiResponse()
        },
        tags=["Users"]
    )
    @action(detail=True, methods=['post'], url_path='change-role', permission_classes=[IsAdmin])
    def change_role(self, request, pk=None):
        """
        修改用户角色
        POST /users/{id}/change-role
        Body: {"role": "admin"}
        """
        user = self.get_object()
        role = request.data.get('role')
        
        if role not in [choice[0] for choice in User.Role.choices]:
            return error_response(
                message='Invalid role',
                code=400,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        user.role = role
        user.save()
        
        serializer = UserSerializer(user)
        return success_response(serializer.data, message='Role changed successfully')
    
    @extend_schema(
        request=None,
        responses={
            200: OpenApiResponse(response=UserSerializer),
            403: OpenApiResponse()
        },
        tags=["Users"]
    )
    @action(detail=True, methods=['post'], url_path='toggle-active', permission_classes=[IsAdmin])
    def toggle_active(self, request, pk=None):
        """
        切换用户激活状态
        POST /users/{id}/toggle-active
        """
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        
        serializer = UserSerializer(user)
        return success_response(
            serializer.data,
            message=f"User {'activated' if user.is_active else 'deactivated'} successfully"
        )


# ===== 认证相关视图 =====

from rest_framework.views import APIView

class RoleView(APIView):
    """
    获取所有可用角色
    GET /roles
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=RoleItemSerializer(many=True)
            )
        },
        tags=["Roles"]
    )
    def get(self, request):
        roles = [
            {"value": choice[0], "label": choice[1]}
            for choice in User.Role.choices
        ]
        return success_response(roles)


class LoginView(APIView):
    """
    登录视图
    POST /auth/sso
    """
    permission_classes = [AllowAny]
    google_request = requests.Request()
    
    @extend_schema(
        request=LoginRequestSerializer,
        responses={
            200: OpenApiResponse(response=LoginResponseDataSerializer),
            400: OpenApiResponse(),
            401: OpenApiResponse(),
            403: OpenApiResponse(),
            500: OpenApiResponse()
        },
        auth=[],
        tags=["Authentication"]
    )
    def post(self, request):
        ssoToken = request.data.get('sso_token')
        if not ssoToken:
            return error_response('ssoToken is required', 400, status.HTTP_400_BAD_REQUEST)
        
        from django.conf import settings
        client_id = settings.GOOGLE_OAUTH_CLIENT_ID
        
        if not client_id:
            return error_response('Google OAuth not configured', 500, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Add clock skew tolerance (e.g., 10 seconds) to handle time sync issues
            payload = id_token.verify_oauth2_token(ssoToken, self.google_request, client_id, clock_skew_in_seconds=10)

            email = payload.get('email')
            if not email:
                return error_response('Email not found in token', 400, status.HTTP_400_BAD_REQUEST)
            
            name = payload.get('name', '')
            avatar_url = payload.get('picture', '')
            email_verified = payload.get('email_verified', False)

            if not email_verified:
                return error_response('Email not verified by Google', 403, status.HTTP_403_FORBIDDEN)

            from rest_framework_simplejwt.tokens import RefreshToken

            admin_emails = os.getenv('ADMIN_EMAILS', '').split(',')
            is_admin = email in admin_emails
            
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'name': name,
                    'avatar_url': avatar_url,
                    'is_active': True,
                    'role': User.Role.ADMIN if is_admin else User.Role.END_USER,
                }
            )

            if not created:
                user.name = name
                user.avatar_url = avatar_url
                user.save()

            if not user.is_active:
                return error_response('User account is disabled', 403, status.HTTP_403_FORBIDDEN)

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            # 记录审计日志
            action = 'SSO_LOGIN' if created else 'SSO_LOGIN_EXISTING'
            details = f"User logged in via Google SSO. New user: {created}"
            create_audit_log(user, action, details, request)

            user_serializer = CurrentUserSerializer(user)
            return success_response(
                data={
                    'token': access_token,
                    'user': user_serializer.data
                },
                message='Login successful'
            )
            
        except ValueError as e:
            print(f"SSO Verification Error: {str(e)}") # Debug Log
            return error_response(f'Invalid Google token: {str(e)}', 401, status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            print(f"SSO Unexpected Error: {str(e)}") # Debug Log
            return error_response(f'Authentication failed: {str(e)}', 500, status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutView(APIView):
    """
    登出视图
    POST /auth/logout
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=LogoutRequestSerializer,
        responses={
            200: OpenApiResponse()
        },
        tags=["Authentication"]
    )
    def post(self, request):
        try:
            from rest_framework_simplejwt.tokens import RefreshToken
            
            # 获取 refresh token（从 body 或让客户端传）
            refresh_token = request.data.get('refresh_token')
            
            if refresh_token:
                # 将 refresh token 加入黑名单
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # 记录审计日志
            create_audit_log(request.user, 'LOGOUT', 'User logged out', request)
            
            return success_response(None, message='Logged out successfully')
        except Exception as e:
            # 即使黑名单失败，也返回成功（客户端可以删除本地 token）
            return success_response(None, message='Logged out successfully')


class RefreshTokenView(APIView):
    """
    刷新Token视图
    POST /auth/refresh
    """
    permission_classes = [AllowAny]
    
    @extend_schema(exclude=True)
    def post(self, request):
        # TODO: 实现token刷新逻辑
        # 可使用 simplejwt 的 TokenRefreshView
        return error_response(
            message='Refresh endpoint - to be implemented',
            code=501,
            status_code=status.HTTP_501_NOT_IMPLEMENTED
        )


class CurrentUserView(APIView):
    """
    获取当前用户信息（符合API文档路径 /auth/me）
    GET /auth/me
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={
            200: OpenApiResponse(response=CurrentUserSerializer),
            401: OpenApiResponse()
        },
        tags=["Authentication"]
    )
    def get(self, request):
        serializer = CurrentUserSerializer(request.user)
        return success_response(serializer.data)


# ===== Team Management Views =====

class TeamViewSet(viewsets.ModelViewSet):
    """
    Team ViewSet
    
    提供团队的 CRUD 操作和成员管理
    """
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """根据不同的 action 返回不同的序列化器"""
        if self.action == 'create':
            return TeamCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TeamUpdateSerializer
        return TeamSerializer
    
    def get_permissions(self):
        """根据不同的 action 设置不同的权限"""
        # 管理员和经理可以创建团队
        if self.action == 'create':
            return [IsStaffMember()]
        # 管理员可以更新、删除任何团队
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        # 所有认证用户可以查看
        return [IsAuthenticated()]
    
    def list(self, request, *args, **kwargs):
        """获取团队列表"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """创建团队"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # 返回完整的团队信息
        team = serializer.instance
        response_serializer = TeamSerializer(team)
        return APIResponse(
            data=response_serializer.data,
            message='Team created successfully',
            code=201,
            status_code=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        """获取团队详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """更新团队"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # 返回完整的团队信息
        response_serializer = TeamSerializer(instance)
        return success_response(response_serializer.data, message='Team updated successfully')
    
    def destroy(self, request, *args, **kwargs):
        """删除团队"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return APIResponse(
            data=None,
            message='Team deleted successfully',
            code=200
        )
    
    @extend_schema(
        request=AddTeamMemberSerializer,
        responses={
            200: OpenApiResponse(response=TeamSerializer),
            400: OpenApiResponse(),
            404: OpenApiResponse()
        },
        tags=["Teams"]
    )
    @action(detail=True, methods=['post'], url_path='members')
    def add_member(self, request, pk=None):
        """
        添加团队成员
        POST /teams/{id}/members
        Body: {"userId": 1, "role": "member"}
        """
        team = self.get_object()

        # Normalize incoming keys: accept snake_case (e.g. user_id) and map to serializer camelCase fields
        try:
            incoming = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        except Exception:
            incoming = dict(request.data)

        key_map = {
            'user_id': 'userId',
        }
        for snake, camel in key_map.items():
            if snake in incoming and camel not in incoming:
                incoming[camel] = incoming.pop(snake)

        serializer = AddTeamMemberSerializer(
            data=incoming,
            context={'team': team}
        )
        serializer.is_valid(raise_exception=True)
        
        # 添加成员
        user_id = serializer.validated_data['userId']
        role = serializer.validated_data['role']
        user = User.objects.get(id=user_id)
        
        membership = TeamMembership.objects.create(
            team=team,
            user=user,
            role=role
        )
        
        # 如果角色是 leader，更新团队的 leader 字段
        if role == 'leader':
            team.leader = user
            team.save()
        
        # 返回更新后的团队信息
        team_serializer = TeamSerializer(team)
        return success_response(
            team_serializer.data,
            message='Member added successfully'
        )
    
    @extend_schema(
        request=None,
        responses={
            200: OpenApiResponse(response=TeamSerializer),
            404: OpenApiResponse()
        },
        tags=["Teams"]
    )
    @action(detail=True, methods=['delete'], url_path='members/(?P<user_id>[^/.]+)')
    def remove_member(self, request, pk=None, user_id=None):
        """
        移除团队成员
        DELETE /teams/{id}/members/{userId}
        """
        team = self.get_object()
        
        try:
            membership = TeamMembership.objects.get(team=team, user_id=user_id)
            membership.delete()
            
            # 如果移除的是 leader，清除团队的 leader
            if team.leader_id == int(user_id):
                team.leader = None
                team.save()
            
            # 返回更新后的团队信息
            team_serializer = TeamSerializer(team)
            return success_response(
                team_serializer.data,
                message='Member removed successfully'
            )
        except TeamMembership.DoesNotExist:
            return error_response(
                message='Member not found in this team',
                code=404,
                status_code=status.HTTP_404_NOT_FOUND
            )


# ===== Audit Log Views =====

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Audit Log ViewSet (只读)
    
    管理员和经理可访问
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminOrManager]  # Changed from IsAdmin to allow Manager access
    pagination_class = CustomPagination
    
    def get_queryset(self):
        """支持过滤参数"""
        queryset = super().get_queryset()
        
        # 按用户过滤
        user_id = self.request.query_params.get('userId')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # 按操作类型过滤
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action__icontains=action)
        
        # 按日期范围过滤
        start_date = self.request.query_params.get('startDate')
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        
        end_date = self.request.query_params.get('endDate')
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """获取审计日志列表"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return APIResponse(
                data=paginated_response.data,
                message='Success',
                code=200
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    通知视图集
    
    提供通知的查询和标记已读操作
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get_queryset(self):
        """返回当前用户的通知"""
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """
        获取当前用户的通知列表
        支持查询参数: page, pageSize, isRead
        """
        queryset = self.get_queryset()
        
        # 按已读状态过滤
        is_read = request.query_params.get('isRead')
        if is_read is not None:
            is_read_bool = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read_bool)
        
        # 按类型过滤
        notification_type = request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(type=notification_type)
        
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return APIResponse(
                data=paginated_response.data,
                message='Success',
                code=200
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """获取未读通知数量"""
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return success_response({'count': count})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """标记单条通知为已读"""
        notification = get_object_or_404(
            Notification,
            id=pk,
            recipient=request.user
        )
        
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
        
        serializer = self.get_serializer(notification)
        return success_response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """标记所有通知为已读"""
        now = timezone.now()
        updated = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True, read_at=now)
        
        return success_response({
            'message': f'{updated} notifications marked as read',
            'count': updated
        })
    
    def destroy(self, request, *args, **kwargs):
        """删除通知"""
        notification = self.get_object()
        if notification.recipient != request.user:
            return error_response(
                message='Cannot delete other user notifications',
                code=403
            )
        notification.delete()
        return success_response({'message': 'Notification deleted'})
    
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """清除所有已读通知"""
        deleted, _ = Notification.objects.filter(
            recipient=request.user,
            is_read=True
        ).delete()
        
        return success_response({
            'message': f'{deleted} notifications deleted',
            'count': deleted
        })


class NotificationPreferenceViewSet(viewsets.ViewSet):
    """
    通知偏好设置视图集
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """获取当前用户的通知偏好设置"""
        preferences, _ = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = NotificationPreferenceSerializer(preferences)
        return success_response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_preferences(self, request):
        """更新通知偏好设置"""
        preferences, _ = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        
        serializer = NotificationPreferenceSerializer(
            preferences,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return success_response(serializer.data)
        
        return error_response(
            message='Invalid data',
            code=400,
            errors=serializer.errors
        )
