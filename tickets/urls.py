from django.urls import path
from .views import TicketListCreateView, list_categories, list_tickets, get_ticket_detail, add_ticket_comment, change_ticket_status, assign_ticket, update_ticket, submit_satisfaction

urlpatterns = [
    path("tickets/", TicketListCreateView.as_view()),
    path("tickets/list", list_tickets),
    path("tickets/categories", list_categories),
    path("tickets/<uuid:ticket_id>", get_ticket_detail),
    path("tickets/<uuid:ticket_id>/comments", add_ticket_comment),
    path("tickets/<uuid:ticket_id>/status", change_ticket_status),
    path("tickets/<uuid:ticket_id>/assign", assign_ticket),
    path("tickets/<uuid:ticket_id>/update", update_ticket),
    path("tickets/<uuid:ticket_id>/satisfaction", submit_satisfaction),
]
