from rest_framework import serializers
from .models import Ticket, TicketCategory, TicketComment, TicketStatusHistory

class TicketCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(allow_blank=True, required=False, default="")
    category_id = serializers.UUIDField()
    priority = serializers.ChoiceField(choices=["low", "medium", "high", "urgent"])

    def validate_category_id(self, value):
        if not TicketCategory.objects.filter(id=value).exists():
            raise serializers.ValidationError("category_id not found")
        return value

class TicketCategorySerializer(serializers.ModelSerializer):
    parentId = serializers.UUIDField(source="parent_id", allow_null=True, required=False)

    class Meta:
        model = TicketCategory
        fields = ["id", "name", "description", "parentId"]

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

class TicketDetailSerializer(serializers.ModelSerializer):
    category = TicketCategorySerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "category",
            "channel",
            "requester_id",
            "requester_name",
            "requester_email",
            "assignee_id",
            "assignee_name",
            "team_id",
            "team_name",
            "sla_response_deadline",
            "sla_resolution_deadline",
            "sla_breached",
            "satisfaction_rating",
            "satisfaction_comment",
            "created_at",
            "updated_at",
            "resolved_at",
            "closed_at",
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
    
class TicketStatusChangeSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        "new", "assigned", "in_progress", "pending_user", "resolved", "closed"
    ])
    comment = serializers.CharField(required=False, allow_blank=True)

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

class TicketAssignSerializer(serializers.Serializer):
    assignee_id = serializers.CharField()
    team_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class TicketUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)

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