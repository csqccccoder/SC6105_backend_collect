from rest_framework import serializers
from .models import Ticket, TicketCategory, TicketComment, TicketStatusHistory, TicketAttachment, SLAConfig


class TicketCategorySerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=TicketCategory.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = TicketCategory
        fields = ["id", "name", "description", "parent"]

class TicketCreateSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=TicketCategory.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Ticket
        fields = ["title", "description", "priority", "category_id"]

class TicketListItemSerializer(serializers.ModelSerializer):
    category = TicketCategorySerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "title",
            "status",
            "priority",
            "category",
            "channel",
            "requester_id",
            "requester_name",
            "assignee_id",
            "assignee_name",
            "team_id",
            "team_name",
            "sla_breached",
            "created_at",
            "updated_at",
        ]

class TicketCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketComment
        fields = ["content", "is_internal"]

class TicketCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketComment
        fields = [
            "id",
            "content",
            "is_internal",
            "author_id",
            "author_name",
            "author_email",
            "created_at",
        ]

class TicketStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketStatusHistory
        fields = [
            "id",
            "from_status",
            "to_status",
            "comment",
            "changed_by_id",
            "changed_by_name",
            "changed_at",
        ]

class TicketDetailSerializer(serializers.ModelSerializer):
    category = TicketCategorySerializer(read_only=True)
    attachments = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    status_history = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            "id", "title", "description", "status", "priority",
            "category", "channel",
            "requester_id", "requester_name", "requester_email",
            "assignee_id", "assignee_name",
            "team_id", "team_name",
            "attachments", "comments", "status_history",
            "sla_response_deadline", "sla_resolution_deadline", "sla_breached",
            "satisfaction_rating", "satisfaction_comment",
            "created_at", "updated_at", "resolved_at", "closed_at",
        ]

    def get_attachments(self, obj):
        qs = self._get_related_queryset(obj, "attachments", "ticketattachment_set")
        if qs is None:
            return []
        return TicketAttachmentSerializer(qs.order_by("-uploaded_at"), many=True, context=self.context).data

    def _get_related_queryset(self, obj, preferred_related_name: str, fallback_attr: str):
        # 兼容模型里是否设置 related_name
        rel = getattr(obj, preferred_related_name, None)
        if rel is not None and hasattr(rel, "all"):
            return rel.all()
        rel = getattr(obj, fallback_attr, None)
        if rel is not None and hasattr(rel, "all"):
            return rel.all()
        return None

    def get_comments(self, obj):
        qs = self._get_related_queryset(obj, "comments", "ticketcomment_set")
        if qs is None:
            return []
        return TicketCommentSerializer(qs.order_by("created_at"), many=True).data

    def get_status_history(self, obj):
        qs = self._get_related_queryset(obj, "status_histories", "ticketstatushistory_set")
        if qs is None:
            return []
        return TicketStatusHistorySerializer(qs.order_by("changed_at"), many=True).data

class TicketAssignSerializer(serializers.Serializer):
    assignee_id = serializers.CharField()
    team_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class TicketStatusChangeSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        "new", "assigned", "in_progress", "pending_user", "resolved", "closed"
    ])
    comment = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class TicketUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, max_length=200)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    priority = serializers.ChoiceField(
        required=False,
        choices=["low", "medium", "high", "urgent"],
    )

    category_id = serializers.UUIDField(required=False)

    assignee_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    team_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_category_id(self, value):
        if not TicketCategory.objects.filter(id=value).exists():
            raise serializers.ValidationError("categoryId not found")
        return value

class TicketSatisfactionSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class TicketAttachmentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    
    class Meta:
        model = TicketAttachment
        fields = ['id', 'filename', 'url', 'file_size', 'mime_type', 'uploaded_at', 'uploaded_by_id', 'uploaded_by_name']
    
    def get_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class SLAConfigSerializer(serializers.ModelSerializer):
    """Serializer for SLA Configuration"""
    responseTime = serializers.IntegerField(source='response_time', required=True)
    resolutionTime = serializers.IntegerField(source='resolution_time', required=True)
    isActive = serializers.BooleanField(source='is_active', required=False, default=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    
    class Meta:
        model = SLAConfig
        fields = ['id', 'priority', 'responseTime', 'resolutionTime', 'description', 'isActive', 'createdAt', 'updatedAt']
        extra_kwargs = {
            'description': {'required': False, 'default': ''},
        }
