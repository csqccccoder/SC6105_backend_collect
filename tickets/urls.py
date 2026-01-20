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
)

urlpatterns = [
    path("tickets/", TicketListCreateView.as_view(), name="ticket-list-create"),
    path("tickets/categories", TicketCategoryListView.as_view(), name="ticket-categories"),
    path("tickets/<uuid:ticket_id>/", TicketDetailView.as_view(), name="ticket-detail"),
    path("tickets/<uuid:ticket_id>/update", TicketUpdateView.as_view(), name="ticket-update"),
    path("tickets/<uuid:ticket_id>/assign", TicketAssignView.as_view(), name="ticket-assign"),
    path("tickets/<uuid:ticket_id>/status", TicketStatusChangeView.as_view(), name="ticket-status"),
    path("tickets/<uuid:ticket_id>/comments", TicketCommentCreateView.as_view(), name="ticket-comment-create"),
    path("tickets/<uuid:ticket_id>/satisfaction", TicketSatisfactionView.as_view(), name="ticket-satisfaction"),
]
