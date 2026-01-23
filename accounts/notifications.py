"""
Notification Service Module
Handles creating and sending notifications (in-app and email)
"""

import logging
from typing import Optional, List
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

from .models import User, Notification, NotificationPreference

logger = logging.getLogger(__name__)


def get_or_create_preferences(user: User) -> NotificationPreference:
    """Get or create notification preferences for a user"""
    prefs, created = NotificationPreference.objects.get_or_create(user=user)
    return prefs


def should_send_email(user: User, notification_type: str) -> bool:
    """Check if email should be sent for this notification type"""
    prefs = get_or_create_preferences(user)
    
    type_mapping = {
        'ticket_created': prefs.email_ticket_created,
        'ticket_assigned': prefs.email_ticket_assigned,
        'ticket_status_changed': prefs.email_ticket_status_changed,
        'ticket_comment': prefs.email_ticket_comment,
        'sla_warning': prefs.email_sla_warning,
        'sla_breached': prefs.email_sla_warning,
        'system': prefs.email_system,
        'mention': prefs.email_ticket_comment,
    }
    
    return type_mapping.get(notification_type, False)


def should_send_inapp(user: User, notification_type: str) -> bool:
    """Check if in-app notification should be created"""
    prefs = get_or_create_preferences(user)
    
    type_mapping = {
        'ticket_created': prefs.inapp_ticket_created,
        'ticket_assigned': prefs.inapp_ticket_assigned,
        'ticket_status_changed': prefs.inapp_ticket_status_changed,
        'ticket_comment': prefs.inapp_ticket_comment,
        'sla_warning': prefs.inapp_sla_warning,
        'sla_breached': prefs.inapp_sla_warning,
        'system': prefs.inapp_system,
        'mention': prefs.inapp_ticket_comment,
    }
    
    return type_mapping.get(notification_type, True)


def send_notification_email(
    recipient: User,
    subject: str,
    message: str,
    html_message: Optional[str] = None
) -> bool:
    """Send email notification"""
    try:
        if not recipient.email:
            logger.warning(f"User {recipient.id} has no email address")
            return False
        
        # Use plain text if no HTML provided
        if html_message is None:
            html_message = f"<html><body><p>{message}</p></body></html>"
        
        send_mail(
            subject=subject,
            message=strip_tags(message),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email sent to {recipient.email}: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient.email}: {str(e)}")
        return False


def create_notification(
    recipient: User,
    notification_type: str,
    title: str,
    message: str,
    related_object_type: Optional[str] = None,
    related_object_id: Optional[str] = None,
    send_email: bool = True
) -> Optional[Notification]:
    """
    Create a notification for a user
    
    Args:
        recipient: User to notify
        notification_type: Type of notification (from Notification.NotificationType)
        title: Notification title
        message: Notification message
        related_object_type: Type of related object (e.g., 'ticket')
        related_object_id: ID of related object
        send_email: Whether to also send an email (will check user preferences)
    
    Returns:
        Created Notification object or None
    """
    notification = None
    
    # Check if in-app notification should be created
    if should_send_inapp(recipient, notification_type):
        notification = Notification.objects.create(
            recipient=recipient,
            type=notification_type,
            title=title,
            message=message,
            related_object_type=related_object_type,
            related_object_id=related_object_id,
        )
        logger.info(f"In-app notification created for {recipient.email}: {title}")
    
    # Check if email should be sent
    if send_email and should_send_email(recipient, notification_type):
        email_sent = send_notification_email(
            recipient=recipient,
            subject=f"[Ticket System] {title}",
            message=message,
        )
        
        if notification and email_sent:
            notification.email_sent = True
            notification.email_sent_at = timezone.now()
            notification.save(update_fields=['email_sent', 'email_sent_at'])
    
    return notification


def notify_ticket_created(ticket, creator: User):
    """Notify relevant users when a ticket is created"""
    from .models import User as UserModel
    
    # Notify all support staff and managers about new ticket
    staff_users = UserModel.objects.filter(
        role__in=[UserModel.Role.SUPPORT_STAFF, UserModel.Role.MANAGER, UserModel.Role.ADMIN],
        is_active=True
    ).exclude(id=creator.id)
    
    for user in staff_users:
        create_notification(
            recipient=user,
            notification_type='ticket_created',
            title=f"New Ticket: {ticket.title}",
            message=f"A new ticket has been created by {creator.name or creator.email}.\n\nTitle: {ticket.title}\nPriority: {ticket.priority}\nCategory: {ticket.category.name if ticket.category else 'N/A'}",
            related_object_type='ticket',
            related_object_id=str(ticket.id),
        )


def notify_ticket_assigned(ticket, assignee: User, assigner: User):
    """Notify user when a ticket is assigned to them"""
    if assignee.id == assigner.id:
        return  # Don't notify if self-assigning
    
    create_notification(
        recipient=assignee,
        notification_type='ticket_assigned',
        title=f"Ticket Assigned: {ticket.title}",
        message=f"You have been assigned to ticket: {ticket.title}\n\nAssigned by: {assigner.name or assigner.email}\nPriority: {ticket.priority}",
        related_object_type='ticket',
        related_object_id=str(ticket.id),
    )


def notify_ticket_status_changed(ticket, old_status: str, new_status: str, changed_by: User):
    """Notify ticket requester when status changes"""
    from .models import User as UserModel
    
    # Notify the ticket requester
    try:
        requester = UserModel.objects.get(id=ticket.requester_id)
        if requester.id != changed_by.id:
            create_notification(
                recipient=requester,
                notification_type='ticket_status_changed',
                title=f"Ticket Status Updated: {ticket.title}",
                message=f"Your ticket status has been changed.\n\nTicket: {ticket.title}\nOld Status: {old_status}\nNew Status: {new_status}\nUpdated by: {changed_by.name or changed_by.email}",
                related_object_type='ticket',
                related_object_id=str(ticket.id),
            )
    except UserModel.DoesNotExist:
        logger.warning(f"Requester not found for ticket {ticket.id}")
    
    # If ticket has an assignee, notify them too
    if ticket.assignee_id and str(ticket.assignee_id) != str(changed_by.id):
        try:
            assignee = UserModel.objects.get(id=ticket.assignee_id)
            create_notification(
                recipient=assignee,
                notification_type='ticket_status_changed',
                title=f"Assigned Ticket Updated: {ticket.title}",
                message=f"A ticket assigned to you has been updated.\n\nTicket: {ticket.title}\nOld Status: {old_status}\nNew Status: {new_status}\nUpdated by: {changed_by.name or changed_by.email}",
                related_object_type='ticket',
                related_object_id=str(ticket.id),
            )
        except UserModel.DoesNotExist:
            pass


def notify_new_comment(ticket, comment, commenter: User):
    """Notify relevant users when a new comment is added"""
    from .models import User as UserModel
    
    # Skip internal comments for end users
    if comment.is_internal:
        # Only notify staff members
        recipients = []
        if ticket.assignee_id and str(ticket.assignee_id) != str(commenter.id):
            try:
                assignee = UserModel.objects.get(id=ticket.assignee_id)
                recipients.append(assignee)
            except UserModel.DoesNotExist:
                pass
    else:
        # Notify requester and assignee
        recipients = []
        
        # Notify requester
        if str(ticket.requester_id) != str(commenter.id):
            try:
                requester = UserModel.objects.get(id=ticket.requester_id)
                recipients.append(requester)
            except UserModel.DoesNotExist:
                pass
        
        # Notify assignee
        if ticket.assignee_id and str(ticket.assignee_id) != str(commenter.id):
            try:
                assignee = UserModel.objects.get(id=ticket.assignee_id)
                if assignee not in recipients:
                    recipients.append(assignee)
            except UserModel.DoesNotExist:
                pass
    
    for recipient in recipients:
        create_notification(
            recipient=recipient,
            notification_type='ticket_comment',
            title=f"New Comment on: {ticket.title}",
            message=f"A new comment has been added to the ticket.\n\nTicket: {ticket.title}\nComment by: {commenter.name or commenter.email}\n\n{comment.content[:200]}{'...' if len(comment.content) > 200 else ''}",
            related_object_type='ticket',
            related_object_id=str(ticket.id),
        )


def notify_sla_warning(ticket, warning_type: str = 'warning'):
    """Notify assignee and managers about SLA warning/breach"""
    from .models import User as UserModel
    
    notification_type = 'sla_breached' if warning_type == 'breached' else 'sla_warning'
    title_prefix = "SLA BREACHED" if warning_type == 'breached' else "SLA Warning"
    
    recipients = []
    
    # Notify assignee
    if ticket.assignee_id:
        try:
            assignee = UserModel.objects.get(id=ticket.assignee_id)
            recipients.append(assignee)
        except UserModel.DoesNotExist:
            pass
    
    # Notify managers
    managers = UserModel.objects.filter(
        role__in=[UserModel.Role.MANAGER, UserModel.Role.ADMIN],
        is_active=True
    )
    for manager in managers:
        if manager not in recipients:
            recipients.append(manager)
    
    for recipient in recipients:
        create_notification(
            recipient=recipient,
            notification_type=notification_type,
            title=f"{title_prefix}: {ticket.title}",
            message=f"Ticket SLA {'has been breached' if warning_type == 'breached' else 'is at risk'}.\n\nTicket: {ticket.title}\nPriority: {ticket.priority}\nStatus: {ticket.status}",
            related_object_type='ticket',
            related_object_id=str(ticket.id),
        )


def notify_system(recipients: List[User], title: str, message: str):
    """Send system notification to multiple users"""
    for recipient in recipients:
        create_notification(
            recipient=recipient,
            notification_type='system',
            title=title,
            message=message,
        )
