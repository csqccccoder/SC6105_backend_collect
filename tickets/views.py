from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.parsers import MultiPartParser, FormParser

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

from .models import Ticket, TicketCategory, TicketComment, TicketStatusHistory, TicketAttachment, SLAConfig
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
    TicketAttachmentSerializer,
    SLAConfigSerializer,
)

from accounts.permissions import IsStaffMember, IsAdminOrManager
from accounts.models import User
from accounts.response_wrapper import success_response, error_response, APIResponse
from accounts.pagination import CustomPagination


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
    pagination_class = CustomPagination

    def get_queryset(self):
        qs = Ticket.objects.all().order_by("-created_at")
        # 非 staff 只能看自己的
        if not _is_staff(self.request.user):
            qs = qs.filter(requester_id=str(self.request.user.id))
        
        # Support status filter
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        # Support keyword search
        keyword = self.request.query_params.get('keyword')
        if keyword:
            qs = qs.filter(title__icontains=keyword)
        
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

    def list(self, request, *args, **kwargs):
        """List tickets with pagination wrapped in standard response"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return APIResponse(
                data=paginated_response.data,
                message='Success',
                code=200
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

    def create(self, request, *args, **kwargs):
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        self.perform_create(create_serializer)

        ticket = create_serializer.instance
        detail_data = TicketDetailSerializer(ticket, context={"request": request}).data
        return success_response(detail_data, message='Ticket created successfully')


class TicketCategoryListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = TicketCategory.objects.all().order_by("name")
    serializer_class = TicketCategorySerializer
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)


class TicketCategoryCreateView(GenericAPIView):
    """Create a new ticket category (manager/admin only)"""
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    serializer_class = TicketCategorySerializer

    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        category = TicketCategory.objects.create(
            name=ser.validated_data["name"],
            description=ser.validated_data.get("description", ""),
            parent=ser.validated_data.get("parent"),
        )
        out = TicketCategorySerializer(category).data
        return success_response(out, message='Category created successfully')


class TicketCategoryDetailView(GenericAPIView):
    """Get, update or delete a ticket category (manager/admin only)"""
    permission_classes = [IsAuthenticated]
    serializer_class = TicketCategorySerializer

    def get_object(self):
        return get_object_or_404(TicketCategory, id=self.kwargs["category_id"])

    def get(self, request, category_id):
        category = self.get_object()
        out = TicketCategorySerializer(category).data
        return success_response(out)

    def put(self, request, category_id):
        if not IsAdminOrManager().has_permission(request, self):
            return error_response("Permission denied", code=403, status_code=403)
        
        category = self.get_object()
        ser = self.get_serializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        
        if "name" in ser.validated_data:
            category.name = ser.validated_data["name"]
        if "description" in ser.validated_data:
            category.description = ser.validated_data["description"]
        if "parent" in ser.validated_data:
            category.parent = ser.validated_data["parent"]
        
        category.save()
        out = TicketCategorySerializer(category).data
        return success_response(out, message='Category updated successfully')

    def delete(self, request, category_id):
        if not IsAdminOrManager().has_permission(request, self):
            return error_response("Permission denied", code=403, status_code=403)
        
        category = self.get_object()
        # Check if category has tickets
        if category.tickets.exists():
            return error_response("Cannot delete category with existing tickets", code=400, status_code=400)
        category.delete()
        return success_response(None, message='Category deleted successfully')


class TicketDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Ticket.objects.all()
    serializer_class = TicketDetailSerializer
    lookup_url_kwarg = "ticket_id"

    def retrieve(self, request, *args, **kwargs):
        ticket = self.get_object()

        # 非 staff 只能看自己的 ticket
        if not _is_staff(request.user) and not _is_owner(request.user, ticket):
            return error_response("Not allowed", code=403, status_code=403)

        data = self.get_serializer(ticket).data
        return success_response(data)


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
        return success_response(out, message='Ticket updated successfully')


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
        return success_response(out, message='Ticket assigned successfully')


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
        return success_response(out, message='Ticket status updated')


@extend_schema(request=TicketCommentCreateSerializer, responses={201: TicketCommentSerializer})
class TicketCommentCreateView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TicketCommentCreateSerializer

    def post(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id)

        if not _is_staff(request.user) and not _is_owner(request.user, ticket):
            return error_response("Not allowed", code=403, status_code=403)

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
        return success_response(out, message='Comment added')


@extend_schema(request=TicketSatisfactionSerializer, responses={200: TicketDetailSerializer})
class TicketSatisfactionView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TicketSatisfactionSerializer

    def post(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id)

        if not _is_owner(request.user, ticket):
            return error_response("Not allowed", code=403, status_code=403)

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        ticket.satisfaction_rating = data["rating"]
        ticket.satisfaction_comment = data.get("comment")
        ticket.updated_at = timezone.now()
        ticket.save()

        out = TicketDetailSerializer(ticket, context={"request": request}).data
        return success_response(out, message='Feedback submitted')


class TicketAttachmentUploadView(GenericAPIView):
    """Upload attachment to a ticket"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = TicketAttachmentSerializer

    def post(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id)

        # Check permission: owner or staff
        if not _is_staff(request.user) and not _is_owner(request.user, ticket):
            return error_response("Not allowed", code=403, status_code=403)

        file = request.FILES.get('file')
        if not file:
            return error_response("No file provided", code=400, status_code=400)

        # Validate file size (max 10MB)
        if file.size > 10 * 1024 * 1024:
            return error_response("File too large. Maximum size is 10MB", code=400, status_code=400)

        attachment = TicketAttachment.objects.create(
            ticket=ticket,
            filename=file.name,
            file=file,
            file_size=file.size,
            mime_type=file.content_type or '',
            uploaded_by_id=str(request.user.id),
            uploaded_by_name=_get_user_display_name(request.user),
        )

        out = TicketAttachmentSerializer(attachment, context={"request": request}).data
        return success_response(out, message='File uploaded successfully')


class TicketAttachmentDeleteView(GenericAPIView):
    """Delete attachment from a ticket"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, ticket_id, attachment_id):
        ticket = get_object_or_404(Ticket, id=ticket_id)
        attachment = get_object_or_404(TicketAttachment, id=attachment_id, ticket=ticket)

        # Check permission: owner or staff
        if not _is_staff(request.user) and not _is_owner(request.user, ticket):
            return error_response("Not allowed", code=403, status_code=403)

        # Delete the file from storage
        if attachment.file:
            attachment.file.delete(save=False)
        
        attachment.delete()
        return success_response(None, message='Attachment deleted')


class SLAConfigListCreateView(ListCreateAPIView):
    """List and create SLA configurations"""
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    serializer_class = SLAConfigSerializer
    queryset = SLAConfig.objects.all().order_by('priority')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Check if SLA config for this priority already exists
            priority = serializer.validated_data.get('priority')
            if SLAConfig.objects.filter(priority=priority).exists():
                return error_response(f"SLA configuration for priority '{priority}' already exists", code=400, status_code=400)
            serializer.save()
            return success_response(serializer.data, message='SLA configuration created')
        return error_response(serializer.errors, code=400, status_code=400)


class SLAConfigDetailView(GenericAPIView):
    """Retrieve, update or delete an SLA configuration"""
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    serializer_class = SLAConfigSerializer
    
    def get_object(self, sla_id):
        return get_object_or_404(SLAConfig, id=sla_id)
    
    def get(self, request, sla_id):
        sla = self.get_object(sla_id)
        serializer = self.get_serializer(sla)
        return success_response(serializer.data)
    
    def put(self, request, sla_id):
        sla = self.get_object(sla_id)
        serializer = self.get_serializer(sla, data=request.data, partial=True)
        if serializer.is_valid():
            # If priority is being changed, check for duplicates
            new_priority = serializer.validated_data.get('priority')
            if new_priority and new_priority != sla.priority:
                if SLAConfig.objects.filter(priority=new_priority).exists():
                    return error_response(f"SLA configuration for priority '{new_priority}' already exists", code=400, status_code=400)
            serializer.save()
            return success_response(serializer.data, message='SLA configuration updated')
        return error_response(serializer.errors, code=400, status_code=400)
    
    def delete(self, request, sla_id):
        sla = self.get_object(sla_id)
        sla.delete()
        return success_response(None, message='SLA configuration deleted')
