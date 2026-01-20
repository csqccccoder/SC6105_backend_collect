from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import (
    ListCreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    GenericAPIView,
)
from drf_spectacular.utils import extend_schema

from .models import Ticket, TicketCategory, TicketComment, TicketStatusHistory
from .serializers import (
    TicketCreateSerializer,
    TicketListItemSerializer,
    TicketDetailSerializer,
    TicketCategorySerializer,
    TicketUpdateSerializer,
    TicketAssignSerializer,
    TicketStatusChangeSerializer,
    TicketCommentCreateSerializer,
    TicketCommentSerializer,
    TicketSatisfactionSerializer,
)

from accounts.permissions import IsStaffMember, IsAdminOrManager
from accounts.models import User


def _get_user_display_name(user):
    return getattr(user, "name", None) or getattr(user, "username", None) or "User"


def _is_staff(user):
    return getattr(user, "role", None) in [
        User.Role.ADMIN,
        User.Role.MANAGER,
        User.Role.SUPPORT_STAFF,
    ]


def _is_owner(user, ticket: Ticket):
    return str(ticket.requester_id) == str(user.id)


@extend_schema(
    request=TicketCreateSerializer,
    responses={201: TicketDetailSerializer},
)
class TicketListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Ticket.objects.all().order_by("-created_at")
        # 非 staff 只能看自己的
        if not _is_staff(self.request.user):
            qs = qs.filter(requester_id=str(self.request.user.id))
        return qs

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TicketCreateSerializer
        return TicketListItemSerializer

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(
            status="new",
            channel="web",
            requester_id=str(user.id),
            requester_name=_get_user_display_name(user),
            requester_email=getattr(user, "email", "") or "",
        )

    def create(self, request, *args, **kwargs):
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        self.perform_create(create_serializer)

        ticket = create_serializer.instance
        detail_data = TicketDetailSerializer(ticket, context={"request": request}).data
        return Response(detail_data, status=status.HTTP_201_CREATED)


class TicketCategoryListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = TicketCategory.objects.all().order_by("name")
    serializer_class = TicketCategorySerializer


class TicketDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Ticket.objects.all()
    serializer_class = TicketDetailSerializer
    lookup_url_kwarg = "ticket_id"

    def retrieve(self, request, *args, **kwargs):
        ticket = self.get_object()

        # 非 staff 只能看自己的 ticket
        if not _is_staff(request.user) and not _is_owner(request.user, ticket):
            return Response(
                {"detail": "Not allowed"},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = self.get_serializer(ticket).data
        return Response(data, status=status.HTTP_200_OK)


@extend_schema(request=TicketUpdateSerializer, responses={200: TicketDetailSerializer})
class TicketUpdateView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TicketUpdateSerializer

    def put(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id)

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        if "title" in data:
            ticket.title = data["title"]
        if "description" in data:
            ticket.description = data["description"]
        if "priority" in data:
            ticket.priority = data["priority"]

        if "category_id" in data:
            category = get_object_or_404(TicketCategory, id=data["category_id"])
            ticket.category = category

        if "assignee_id" in data:
            ticket.assignee_id = data["assignee_id"]
        if "team_id" in data:
            ticket.team_id = data["team_id"]

        ticket.updated_at = timezone.now()
        ticket.save()

        out = TicketDetailSerializer(ticket, context={"request": request}).data
        return Response(out, status=status.HTTP_200_OK)


@extend_schema(request=TicketAssignSerializer, responses={200: TicketDetailSerializer})
class TicketAssignView(GenericAPIView):
    permission_classes = [IsAdminOrManager]
    serializer_class = TicketAssignSerializer

    def post(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id)

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        ticket.assignee_id = data["assignee_id"]
        ticket.team_id = data.get("team_id")

        if ticket.status == "new":
            ticket.status = "assigned"

        ticket.updated_at = timezone.now()
        ticket.save()

        out = TicketDetailSerializer(ticket, context={"request": request}).data
        return Response(out, status=status.HTTP_200_OK)


@extend_schema(request=TicketStatusChangeSerializer, responses={200: TicketDetailSerializer})
class TicketStatusChangeView(GenericAPIView):
    permission_classes = [IsStaffMember]
    serializer_class = TicketStatusChangeSerializer

    def post(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id)

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        old_status = ticket.status
        new_status = data["status"]
        comment = data.get("comment", "")

        if old_status != new_status:
            ticket.status = new_status

            TicketStatusHistory.objects.create(
                ticket=ticket,
                from_status=old_status,
                to_status=new_status,
                comment=comment,
                changed_by_id=str(request.user.id),
                changed_by_name=_get_user_display_name(request.user),
                changed_at=timezone.now(),
            )

            if new_status == "resolved":
                ticket.resolved_at = timezone.now()
            if new_status == "closed":
                ticket.closed_at = timezone.now()

        ticket.updated_at = timezone.now()
        ticket.save()

        out = TicketDetailSerializer(ticket, context={"request": request}).data
        return Response(out, status=status.HTTP_200_OK)


@extend_schema(request=TicketCommentCreateSerializer, responses={201: TicketCommentSerializer})
class TicketCommentCreateView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TicketCommentCreateSerializer

    def post(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id)

        if not _is_staff(request.user) and not _is_owner(request.user, ticket):
            return Response(
                {"detail": "Not allowed"},
                status=status.HTTP_403_FORBIDDEN,
            )

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        comment = TicketComment.objects.create(
            ticket=ticket,
            content=data["content"],
            is_internal=data.get("is_internal", False),
            author_id=str(request.user.id),
            author_name=_get_user_display_name(request.user),
            author_email=getattr(request.user, "email", "") or "",
            created_at=timezone.now(),
        )

        out = TicketCommentSerializer(comment, context={"request": request}).data
        return Response(out, status=status.HTTP_201_CREATED)


@extend_schema(request=TicketSatisfactionSerializer, responses={200: TicketDetailSerializer})
class TicketSatisfactionView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TicketSatisfactionSerializer

    def post(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id)

        if not _is_owner(request.user, ticket):
            return Response(
                {"detail": "Not allowed"},
                status=status.HTTP_403_FORBIDDEN,
            )

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        ticket.satisfaction_rating = data["rating"]
        ticket.satisfaction_comment = data.get("comment")
        ticket.updated_at = timezone.now()
        ticket.save()

        out = TicketDetailSerializer(ticket, context={"request": request}).data
        return Response(out, status=status.HTTP_200_OK)
