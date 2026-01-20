import math

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from .models import Ticket, TicketCategory, TicketComment, TicketStatusHistory
from .serializers import TicketCreateSerializer, TicketCategorySerializer, TicketListItemSerializer, TicketDetailSerializer, TicketCommentCreateSerializer, TicketCommentSerializer, TicketStatusChangeSerializer, TicketStatusHistorySerializer, TicketAssignSerializer, TicketUpdateSerializer, TicketSatisfactionSerializer
from rest_framework.generics import ListCreateAPIView
from drf_spectacular.utils import extend_schema

@extend_schema(
    request=TicketCreateSerializer,
    responses={201: TicketDetailSerializer},
)
class TicketListCreateView(ListCreateAPIView):
    queryset = Ticket.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TicketCreateSerializer
        return TicketDetailSerializer

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_ticket(request):
    serializer = TicketCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    category = TicketCategory.objects.get(id=serializer.validated_data["category_id"])

    ticket = Ticket.objects.create(
        title=serializer.validated_data["title"],
        description=serializer.validated_data.get("description", ""),
        category=category,
        priority=serializer.validated_data["priority"],
        status="new",
        channel="web",
        # A 路线：没有登录，就用占位 requester（或允许前端可选传入覆盖）
        requester_id=request.data.get("requesterId", "dev-user"),
        requester_name=request.data.get("requesterName", "Dev User"),
        requester_email=request.data.get("requesterEmail", "dev@example.com"),
    )

    # 按接口文档返回 Ticket 结构（先给空数组：attachments/comments/statusHistory）
    data = {
        "id": str(ticket.id),
        "title": ticket.title,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "category": TicketCategorySerializer(ticket.category).data,
        "channel": ticket.channel,
        "requesterId": ticket.requester_id,
        "requesterName": ticket.requester_name,
        "requesterEmail": ticket.requester_email,
        "assigneeId": ticket.assignee_id,
        "assigneeName": ticket.assignee_name,
        "teamId": ticket.team_id,
        "teamName": ticket.team_name,
        "attachments": [],
        "comments": [],
        "statusHistory": [],
        "slaResponseDeadline": ticket.sla_response_deadline,
        "slaResolutionDeadline": ticket.sla_resolution_deadline,
        "slaBreached": ticket.sla_breached,
        "satisfactionRating": ticket.satisfaction_rating,
        "satisfactionComment": ticket.satisfaction_comment,
        "createdAt": ticket.created_at,
        "updatedAt": ticket.updated_at,
        "resolvedAt": ticket.resolved_at,
        "closedAt": ticket.closed_at,
    }
    return Response(data)  # 你的全局包装会自动包 {code,message,data}

@api_view(["GET"])
@permission_classes([AllowAny])  # 先按 A 路线，不做权限阻塞
def list_categories(request):
    qs = TicketCategory.objects.all().order_by("name")
    data = TicketCategorySerializer(qs, many=True).data
    return Response(data)



@api_view(["GET"])
@permission_classes([AllowAny])  # A 路线：先不做权限阻塞
def list_tickets(request):
    # Query params (camelCase will be converted to snake_case by the parser is for body; for query params we read both)
    page = int(request.query_params.get("page", 1))
    page_size = int(request.query_params.get("pageSize", request.query_params.get("page_size", 10)))

    status_ = request.query_params.get("status")
    priority = request.query_params.get("priority")
    category_id = request.query_params.get("categoryId", request.query_params.get("category_id"))
    assignee_id = request.query_params.get("assigneeId", request.query_params.get("assignee_id"))
    keyword = request.query_params.get("keyword")

    qs = Ticket.objects.select_related("category").all().order_by("-created_at")

    if status_:
        qs = qs.filter(status=status_)
    if priority:
        qs = qs.filter(priority=priority)
    if category_id:
        qs = qs.filter(category_id=category_id)
    if assignee_id:
        qs = qs.filter(assignee_id=assignee_id)
    if keyword:
        qs = qs.filter(Q(title__icontains=keyword) | Q(description__icontains=keyword))

    total = qs.count()
    total_pages = max(1, math.ceil(total / page_size))
    page = max(1, min(page, total_pages))

    start = (page - 1) * page_size
    end = start + page_size
    items = TicketListItemSerializer(qs[start:end], many=True).data

    data = {
        "items": items,
        "page": page,
        "pageSize": page_size,
        "total": total,
        "totalPages": total_pages,
    }
    return Response(data)

@api_view(["GET"])
@permission_classes([AllowAny])  # A 路线：先不做权限阻塞
def get_ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket.objects.select_related("category"), id=ticket_id)
    data = TicketDetailSerializer(ticket).data

    # 按接口文档补齐：先返回空数组，后续再做 Comment/History/Attachment 表
    data["attachments"] = []
    data["comments"] = [TicketCommentSerializer(ticket.comments.all(), many=True).data]
    data["statusHistory"] = [TicketStatusHistorySerializer(ticket.status_histories.all(), many=True).data]

    return Response(data)

@api_view(["POST"])
@permission_classes([AllowAny])
def add_ticket_comment(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    serializer = TicketCommentCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    comment = serializer.save(
        ticket=ticket,
        # A 路线：暂时填占位作者；以后接 auth 后替换为 request.user
        author_id="system",
        author_name="System",
        author_email=None,
    )

    return Response(TicketCommentSerializer(comment).data)

@api_view(["POST"])
@permission_classes([AllowAny])
def change_ticket_status(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    ser = TicketStatusChangeSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    new_status = ser.validated_data["status"]
    comment = ser.validated_data.get("comment", "")

    old_status = ticket.status
    if old_status == new_status:
        # 不强制报错也行，这里选择直接返回当前 ticket 状态
        return Response({"id": str(ticket.id), "status": ticket.status})

    # 1) 更新 Ticket
    ticket.status = new_status

    # 可选：如果你模型里有 resolved_at / closed_at 字段，就顺手维护
    if new_status == "resolved":
        ticket.resolved_at = timezone.now()
    if new_status == "closed":
        ticket.closed_at = timezone.now()

    ticket.save()

    # 2) 写入状态历史
    TicketStatusHistory.objects.create(
        ticket=ticket,
        from_status=old_status,
        to_status=new_status,
        comment=comment or None,
        changed_by_id="system",
        changed_by_name="System",
    )

    # 3) 返回（先简单返回当前状态；也可以按你们前端需要返回整张 Ticket）
    return Response({"id": str(ticket.id), "status": ticket.status})

@api_view(["POST"])
@permission_classes([AllowAny])
def assign_ticket(request, ticket_id):
    
    print("DEBUG request.data =", request.data)
    ticket = get_object_or_404(Ticket, id=ticket_id)

    ser = TicketAssignSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    assignee_id = ser.validated_data["assignee_id"]
    team_id = ser.validated_data.get("team_id")

    # A 路线：没有用户/团队表，先做占位映射（后面接权限模块再替换）
    ticket.assignee_id = assignee_id
    ticket.assignee_name = f"User {assignee_id}"

    if team_id:
        ticket.team_id = team_id
        ticket.team_name = f"Team {team_id}"
    else:
        ticket.team_id = None
        ticket.team_name = None

    # 推荐：分配后自动进入 assigned（如果你们不想自动改状态，删掉这两行即可）
    if ticket.status == "new":
        ticket.status = "assigned"

    ticket.save()

    return Response({
        "id": str(ticket.id),
        "assigneeId": ticket.assignee_id,
        "assigneeName": ticket.assignee_name,
        "teamId": ticket.team_id,
        "teamName": ticket.team_name,
        "status": ticket.status,
    })

@api_view(["PUT"])
@permission_classes([AllowAny])
def update_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    ser = TicketUpdateSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    data = ser.validated_data

    # 简单字段
    if "title" in data:
        ticket.title = data["title"]
    if "description" in data:
        ticket.description = data["description"]
    if "priority" in data:
        ticket.priority = data["priority"]

    # 分类
    if "category_id" in data:
        ticket.category_id = data["category_id"]

    # 分派/团队（允许置空）
    if "assignee_id" in data:
        ticket.assignee_id = data["assignee_id"] or None
        ticket.assignee_name = f"User {ticket.assignee_id}" if ticket.assignee_id else None

    if "team_id" in data:
        ticket.team_id = data["team_id"] or None
        ticket.team_name = f"Team {ticket.team_id}" if ticket.team_id else None

    ticket.save()

    out = TicketDetailSerializer(ticket).data
    out["attachments"] = []
    out["comments"] = [TicketCommentSerializer(ticket.comments.all(), many=True).data]
    out["statusHistory"] = [TicketStatusHistorySerializer(ticket.status_histories.all(), many=True).data]
    return Response(out)

@api_view(["POST"])
@permission_classes([AllowAny])
def submit_satisfaction(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    ser = TicketSatisfactionSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    ticket.satisfaction_rating = ser.validated_data["rating"]
    ticket.satisfaction_comment = ser.validated_data.get("comment") or None
    ticket.save()

    return Response({
        "id": str(ticket.id),
        "satisfactionRating": ticket.satisfaction_rating,
        "satisfactionComment": ticket.satisfaction_comment,
    })