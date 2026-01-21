from django.urls import path

from .views import (
    TicketListCreateView,
    TicketDetailView,
    TicketUpdateView,
    TicketAssignView,
    TicketStatusChangeView,
    TicketCommentCreateView,
    TicketSatisfactionView,
    TicketCategoryListView,
    TicketCategoryCreateView,
    TicketCategoryDetailView,
    TicketAttachmentUploadView,
    TicketAttachmentDeleteView,
    SLAConfigListCreateView,
    SLAConfigDetailView,
)
from .analytics_views import (
    TicketAnalyticsView,
    AgentPerformanceView,
    KnowledgeAnalyticsView,
    SLAAnalyticsView,
)

urlpatterns = [
    path("tickets/", TicketListCreateView.as_view(), name="ticket-list-create"),
    path("tickets/categories", TicketCategoryListView.as_view(), name="ticket-categories"),
    path("tickets/categories/create", TicketCategoryCreateView.as_view(), name="ticket-category-create"),
    path("tickets/categories/<uuid:category_id>", TicketCategoryDetailView.as_view(), name="ticket-category-detail"),
    path("tickets/<uuid:ticket_id>/", TicketDetailView.as_view(), name="ticket-detail"),
    path("tickets/<uuid:ticket_id>/update", TicketUpdateView.as_view(), name="ticket-update"),
    path("tickets/<uuid:ticket_id>/assign", TicketAssignView.as_view(), name="ticket-assign"),
    path("tickets/<uuid:ticket_id>/status", TicketStatusChangeView.as_view(), name="ticket-status"),
    path("tickets/<uuid:ticket_id>/comments", TicketCommentCreateView.as_view(), name="ticket-comment-create"),
    path("tickets/<uuid:ticket_id>/satisfaction", TicketSatisfactionView.as_view(), name="ticket-satisfaction"),
    path("tickets/<uuid:ticket_id>/attachments", TicketAttachmentUploadView.as_view(), name="ticket-attachment-upload"),
    path("tickets/<uuid:ticket_id>/attachments/<uuid:attachment_id>", TicketAttachmentDeleteView.as_view(), name="ticket-attachment-delete"),
    # SLA Configuration
    path("sla/configs/", SLAConfigListCreateView.as_view(), name="sla-config-list-create"),
    path("sla/configs/<uuid:sla_id>/", SLAConfigDetailView.as_view(), name="sla-config-detail"),
    # Analytics
    path("analytics/tickets", TicketAnalyticsView.as_view(), name="analytics-tickets"),
    path("analytics/agents", AgentPerformanceView.as_view(), name="analytics-agents"),
    path("analytics/knowledge", KnowledgeAnalyticsView.as_view(), name="analytics-knowledge"),
    path("analytics/sla", SLAAnalyticsView.as_view(), name="analytics-sla"),
]
