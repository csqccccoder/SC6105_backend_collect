from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom User Model"""

    class Role(models.TextChoices):
        END_USER = 'end_user', 'End User'
        SUPPORT_STAFF = 'support_staff', 'Support Staff'
        MANAGER = 'manager', 'Manager'
        ADMIN = 'admin', 'Admin'

    # === Core Fields ===
    # Override AbstractUser's email field to make it unique and required
    email = models.EmailField('Email Address', unique=True)

    # Name (AbstractUser has first_name/last_name, but we use a single name field)
    name = models.CharField('Name', max_length=100, blank=True, null=True)

    avatar_url = models.URLField('Avatar URL', max_length=255, blank=True, null=True)

    role = models.CharField(
        'Role',
        max_length=20,
        choices=Role.choices,
        default=Role.END_USER,
    )

    # Additional fields required by API spec
    department = models.CharField('Department', max_length=100, blank=True, null=True)
    phone = models.CharField('Phone', max_length=20, blank=True, null=True)

    # === Timestamps ===
    # AbstractUser already has date_joined and last_login
    # We only need to add updated_at
    updated_at = models.DateTimeField('Updated At', auto_now=True)

    # === Authentication Configuration ===
    USERNAME_FIELD = 'email'
    # Required fields (besides email and password) that createsuperuser command will ask for
    # Note: AbstractUser requires username by default, so we include it here
    REQUIRED_FIELDS = ['username', 'name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['role']),
        ]
        # Order by creation time (newest first)
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.name} ({self.email})" if self.name else self.email

    def save(self, *args, **kwargs):
        if self.username is None or self.username == "":
            self.username = self.email
        super().save(*args, **kwargs)


    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER

    @property
    def is_support_staff(self):
        return self.role == self.Role.SUPPORT_STAFF

    @property
    def is_end_user(self):
        return self.role == self.Role.END_USER


class Team(models.Model):
    """Team Model for organizing users"""
    
    name = models.CharField('Team Name', max_length=100)
    description = models.TextField('Description', blank=True, null=True)
    leader = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='led_teams',
        verbose_name='Team Leader'
    )
    created_at = models.DateTimeField('Created At', auto_now_add=True)
    updated_at = models.DateTimeField('Updated At', auto_now=True)
    
    class Meta:
        db_table = 'teams'
        verbose_name = 'Team'
        verbose_name_plural = 'Teams'
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.name
    
    @property
    def member_count(self):
        """Count of team members including leader"""
        return self.memberships.count()
    
    @property
    def active_tickets(self):
        """Count of active tickets assigned to this team"""
        # TODO: Implement when Ticket model is available
        return 0


class TeamMembership(models.Model):
    """Team membership - relationship between User and Team"""
    
    class MemberRole(models.TextChoices):
        LEADER = 'leader', 'Leader'
        MEMBER = 'member', 'Member'
    
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='Team'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='team_memberships',
        verbose_name='User'
    )
    role = models.CharField(
        'Role',
        max_length=10,
        choices=MemberRole.choices,
        default=MemberRole.MEMBER
    )
    joined_at = models.DateTimeField('Joined At', auto_now_add=True)
    
    class Meta:
        db_table = 'team_memberships'
        verbose_name = 'Team Membership'
        verbose_name_plural = 'Team Memberships'
        unique_together = ['team', 'user']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.email} in {self.team.name} ({self.role})"


class AuditLog(models.Model):
    """Audit Log Model for tracking user actions"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name='User'
    )
    user_email = models.EmailField('User Email', max_length=255)
    action = models.CharField('Action', max_length=100)
    details = models.TextField('Details', blank=True, null=True)
    ip_address = models.GenericIPAddressField('IP Address', null=True, blank=True)
    timestamp = models.DateTimeField('Timestamp', auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['action']),
        ]
    
    def __str__(self):
        return f"{self.user_email} - {self.action} - {self.timestamp}"


class Notification(models.Model):
    """Notification Model for in-app and email notifications"""
    
    class NotificationType(models.TextChoices):
        TICKET_CREATED = 'ticket_created', 'Ticket Created'
        TICKET_ASSIGNED = 'ticket_assigned', 'Ticket Assigned'
        TICKET_STATUS_CHANGED = 'ticket_status_changed', 'Ticket Status Changed'
        TICKET_COMMENT = 'ticket_comment', 'New Comment'
        SLA_WARNING = 'sla_warning', 'SLA Warning'
        SLA_BREACHED = 'sla_breached', 'SLA Breached'
        SYSTEM = 'system', 'System Notification'
        MENTION = 'mention', 'You were mentioned'
    
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Recipient'
    )
    type = models.CharField(
        'Type',
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM
    )
    title = models.CharField('Title', max_length=200)
    message = models.TextField('Message')
    
    # Related object (optional) - for linking to ticket, etc.
    related_object_type = models.CharField('Related Object Type', max_length=50, blank=True, null=True)
    related_object_id = models.CharField('Related Object ID', max_length=100, blank=True, null=True)
    
    # Status
    is_read = models.BooleanField('Is Read', default=False)
    read_at = models.DateTimeField('Read At', null=True, blank=True)
    
    # Email notification
    email_sent = models.BooleanField('Email Sent', default=False)
    email_sent_at = models.DateTimeField('Email Sent At', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField('Created At', auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['type']),
        ]
    
    def __str__(self):
        return f"{self.recipient.email} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class NotificationPreference(models.Model):
    """User notification preferences"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name='User'
    )
    
    # Email preferences
    email_ticket_created = models.BooleanField('Email on Ticket Created', default=True)
    email_ticket_assigned = models.BooleanField('Email on Ticket Assigned', default=True)
    email_ticket_status_changed = models.BooleanField('Email on Status Changed', default=True)
    email_ticket_comment = models.BooleanField('Email on New Comment', default=True)
    email_sla_warning = models.BooleanField('Email on SLA Warning', default=True)
    email_system = models.BooleanField('Email System Notifications', default=False)
    
    # In-app preferences
    inapp_ticket_created = models.BooleanField('In-App Ticket Created', default=True)
    inapp_ticket_assigned = models.BooleanField('In-App Ticket Assigned', default=True)
    inapp_ticket_status_changed = models.BooleanField('In-App Status Changed', default=True)
    inapp_ticket_comment = models.BooleanField('In-App New Comment', default=True)
    inapp_sla_warning = models.BooleanField('In-App SLA Warning', default=True)
    inapp_system = models.BooleanField('In-App System Notifications', default=True)
    
    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.email}"
