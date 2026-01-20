from rest_framework import serializers
from .models import User, Team, TeamMembership, AuditLog


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器 - 符合 API 文档规范"""
    
    # 驼峰命名的字段
    isActive = serializers.BooleanField(source='is_active', read_only=True)
    createdAt = serializers.DateTimeField(source='date_joined', read_only=True)
    avatar = serializers.URLField(source='avatar_url', required=False, allow_null=True, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'avatar', 'department', 
                  'phone', 'isActive', 'createdAt']
        read_only_fields = ['id', 'isActive', 'createdAt']


class UserDetailSerializer(serializers.ModelSerializer):
    """用户详情序列化器（包含更多信息）"""
    
    isActive = serializers.BooleanField(source='is_active', read_only=True)
    createdAt = serializers.DateTimeField(source='date_joined', read_only=True)
    avatar = serializers.URLField(source='avatar_url', required=False, allow_null=True, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'avatar', 'department',
                  'phone', 'isActive', 'createdAt', 'updated_at']
        read_only_fields = ['id', 'isActive', 'createdAt', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """创建用户序列化器"""
    avatar = serializers.URLField(source='avatar_url', required=False, allow_null=True, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['email', 'name', 'role', 'department', 'phone', 'avatar']
    
    def create(self, validated_data):
        # 为 SSO 用户创建账号（不需要密码）
        # 设置 username 为 email（AbstractUser 需要 username）
        validated_data['username'] = validated_data['email']
        user = User.objects.create(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """更新用户序列化器"""
    isActive = serializers.BooleanField(source='is_active', required=False)
    avatar = serializers.URLField(source='avatar_url', required=False, allow_null=True, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['name', 'role', 'department', 'phone', 'isActive', 'avatar']


class CurrentUserSerializer(serializers.ModelSerializer):
    """当前用户序列化器（用于 /auth/me 接口）"""
    
    isActive = serializers.BooleanField(source='is_active', read_only=True)
    createdAt = serializers.DateTimeField(source='date_joined', read_only=True)
    avatar = serializers.URLField(source='avatar_url', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'avatar', 'department',
                  'phone', 'isActive', 'createdAt']
        read_only_fields = fields


# ========== Team Serializers ==========

class TeamMemberSerializer(serializers.ModelSerializer):
    """Team member serializer"""
    
    id = serializers.IntegerField(source='pk', read_only=True)
    userId = serializers.IntegerField(source='user.id', read_only=True)
    userName = serializers.CharField(source='user.name', read_only=True)
    userEmail = serializers.EmailField(source='user.email', read_only=True)
    joinedAt = serializers.DateTimeField(source='joined_at', read_only=True)
    
    class Meta:
        model = TeamMembership
        fields = ['id', 'userId', 'userName', 'userEmail', 'role', 'joinedAt']


class TeamSerializer(serializers.ModelSerializer):
    """Team serializer for list and detail views"""
    
    leaderId = serializers.IntegerField(source='leader.id', read_only=True)
    leaderName = serializers.CharField(source='leader.name', read_only=True)
    members = TeamMemberSerializer(source='memberships', many=True, read_only=True)
    memberCount = serializers.IntegerField(source='member_count', read_only=True)
    activeTickets = serializers.IntegerField(source='active_tickets', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'leaderId', 'leaderName', 
                  'members', 'memberCount', 'activeTickets', 'createdAt']
        read_only_fields = ['id', 'leaderId', 'leaderName', 'members', 
                           'memberCount', 'activeTickets', 'createdAt']


class TeamCreateSerializer(serializers.ModelSerializer):
    """Team create serializer"""
    
    class Meta:
        model = Team
        fields = ['name', 'description']
    
    def create(self, validated_data):
        # Create team with current user as leader
        user = self.context['request'].user
        team = Team.objects.create(leader=user, **validated_data)
        
        # Add leader as team member with 'leader' role
        TeamMembership.objects.create(
            team=team,
            user=user,
            role=TeamMembership.MemberRole.LEADER
        )
        
        return team


class TeamUpdateSerializer(serializers.ModelSerializer):
    """Team update serializer"""
    
    class Meta:
        model = Team
        fields = ['name', 'description']


class AddTeamMemberSerializer(serializers.Serializer):
    """Serializer for adding team member"""
    
    userId = serializers.IntegerField()
    role = serializers.ChoiceField(choices=['leader', 'member'])
    
    def validate_userId(self, value):
        """Validate user exists"""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        return value
    
    def validate(self, data):
        """Validate user not already in team"""
        team = self.context.get('team')
        user_id = data['userId']
        
        if TeamMembership.objects.filter(team=team, user_id=user_id).exists():
            raise serializers.ValidationError("User is already a member of this team")
        
        return data


# ========== Audit Log Serializers ==========

class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log serializer"""
    
    userId = serializers.IntegerField(source='user.id', read_only=True)
    userEmail = serializers.EmailField(source='user_email', read_only=True)
    ipAddress = serializers.IPAddressField(source='ip_address', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'userId', 'userEmail', 'action', 'details', 'ipAddress', 'timestamp']
        read_only_fields = fields


# ========== Auth API Serializers ==========

class RoleItemSerializer(serializers.Serializer):
    """Role item serializer for role list response"""
    value = serializers.CharField()
    label = serializers.CharField()


class LoginRequestSerializer(serializers.Serializer):
    """Login request serializer"""
    sso_token = serializers.CharField(help_text="Google SSO token")


class LoginResponseDataSerializer(serializers.Serializer):
    """Login response data serializer"""
    token = serializers.CharField(help_text="JWT access token")
    user = CurrentUserSerializer()


class LogoutRequestSerializer(serializers.Serializer):
    """Logout request serializer"""
    refresh_token = serializers.CharField(required=False, allow_null=True, allow_blank=True, 
                                         help_text="Refresh token to blacklist (optional)")


class RefreshTokenRequestSerializer(serializers.Serializer):
    """Refresh token request serializer"""
    refresh_token = serializers.CharField(help_text="Refresh token")


class ChangeRoleRequestSerializer(serializers.Serializer):
    """Change role request serializer"""
    role = serializers.ChoiceField(choices=User.Role.choices)