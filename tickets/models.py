import uuid
from django.db import models


class TicketStatus(models.TextChoices):
    NEW = "new", "new"
    ASSIGNED = "assigned", "assigned"
    IN_PROGRESS = "in_progress", "in_progress"
    PENDING_USER = "pending_user", "pending_user"
    RESOLVED = "resolved", "resolved"
    CLOSED = "closed", "closed"


class TicketPriority(models.TextChoices):
    LOW = "low", "low"
    MEDIUM = "medium", "medium"
    HIGH = "high", "high"
    URGENT = "urgent", "urgent"


class TicketChannel(models.TextChoices):
    WEB = "web", "web"
    EMAIL = "email", "email"
    PHONE = "phone", "phone"
    MOBILE = "mobile", "mobile"


class TicketCategory(models.Model):
    # Frontend expects id as "string" -> use UUID for clean string ids
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )

    def __str__(self):
        return self.name


class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")

    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.NEW)
    priority = models.CharField(max_length=10, choices=TicketPriority.choices, default=TicketPriority.MEDIUM)

    category = models.ForeignKey(TicketCategory, on_delete=models.PROTECT, related_name="tickets")
    channel = models.CharField(max_length=10, choices=TicketChannel.choices, default=TicketChannel.WEB)

    # Path A: auth handled by teammate, so we store requester/assignee as "string ids" for now
    requester_id = models.CharField(max_length=64, blank=True, default="dev-user")
    requester_name = models.CharField(max_length=100, blank=True, default="Dev User")
    requester_email = models.EmailField(blank=True, default="dev@example.com")


    assignee_id = models.CharField(max_length=64, null=True, blank=True)
    assignee_name = models.CharField(max_length=100, null=True, blank=True, default="")

    team_id = models.CharField(max_length=64, null=True, blank=True)
    team_name = models.CharField(max_length=100, null=True, blank=True, default="")

    # SLA / satisfaction fields from the doc
    sla_response_deadline = models.DateTimeField(null=True, blank=True)
    sla_resolution_deadline = models.DateTimeField(null=True, blank=True)
    sla_breached = models.BooleanField(default=False)

    satisfaction_rating = models.IntegerField(null=True, blank=True)
    satisfaction_comment = models.TextField(null=True, blank=True)

    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class TicketComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey("Ticket", related_name="comments", on_delete=models.CASCADE)

    content = models.TextField()
    is_internal = models.BooleanField(default=False)

    # 你们现在走 A 路线（无登录），先留空/可选。以后接入 auth 再补真实用户
    author_id = models.CharField(max_length=64, null=True, blank=True)
    author_name = models.CharField(max_length=128, null=True, blank=True)
    author_email = models.EmailField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class TicketAttachment(models.Model):
    """Ticket attachment model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey("Ticket", related_name="attachments", on_delete=models.CASCADE)
    
    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='ticket_attachments/%Y/%m/%d/')
    file_size = models.IntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True, default='')
    
    uploaded_by_id = models.CharField(max_length=64, null=True, blank=True)
    uploaded_by_name = models.CharField(max_length=128, null=True, blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-uploaded_at"]
    
    def __str__(self):
        return f"{self.filename} ({self.ticket_id})"


class TicketStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey("Ticket", related_name="status_histories", on_delete=models.CASCADE)

    from_status = models.CharField(max_length=32)
    to_status = models.CharField(max_length=32)
    comment = models.TextField(null=True, blank=True)

    # A 路线：先占位；以后接入 auth 再替换为真实用户
    changed_by_id = models.CharField(max_length=64, null=True, blank=True)
    changed_by_name = models.CharField(max_length=128, null=True, blank=True)

    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["changed_at"]


class SLAConfig(models.Model):
    """SLA Configuration model for different priority levels"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    priority = models.CharField(max_length=10, choices=TicketPriority.choices, unique=True)
    response_time = models.IntegerField(help_text="Response time in hours")
    resolution_time = models.IntegerField(help_text="Resolution time in hours")
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "SLA Configuration"
        verbose_name_plural = "SLA Configurations"
        ordering = ["priority"]
    
    def __str__(self):
        return f"SLA for {self.priority}: {self.response_time}h response, {self.resolution_time}h resolution"