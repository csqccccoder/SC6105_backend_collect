"""
Analytics Views
"""
from django.db.models import Count, Avg, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdminOrManager
from accounts.response_wrapper import success_response, error_response
from tickets.models import Ticket, TicketCategory


class TicketAnalyticsView(APIView):
    """
    Ticket Analytics API
    """
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def get(self, request):
        # Get date range from params
        date_from = request.query_params.get('dateFrom')
        date_to = request.query_params.get('dateTo')
        
        # Default to last 30 days
        if not date_to:
            date_to = timezone.now()
        else:
            date_to = timezone.datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        
        if not date_from:
            date_from = date_to - timedelta(days=30)
        else:
            date_from = timezone.datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        
        # Base queryset
        tickets = Ticket.objects.filter(created_at__range=[date_from, date_to])
        
        # Total counts
        total_created = tickets.count()
        total_open = tickets.filter(status__in=['new', 'assigned', 'in_progress', 'pending_user']).count()
        total_closed = tickets.filter(status__in=['resolved', 'closed']).count()
        
        # By status
        by_status = {}
        status_counts = tickets.values('status').annotate(count=Count('id'))
        for item in status_counts:
            by_status[item['status']] = item['count']
        
        # By priority
        by_priority = {}
        priority_counts = tickets.values('priority').annotate(count=Count('id'))
        for item in priority_counts:
            by_priority[item['priority']] = item['count']
        
        # By category
        by_category = []
        category_counts = tickets.values('category__name').annotate(count=Count('id'))
        for item in category_counts:
            by_category.append({
                'name': item['category__name'] or 'Uncategorized',
                'count': item['count']
            })
        
        # Calculate average resolution time (in hours)
        resolved_tickets = tickets.filter(resolved_at__isnull=False)
        avg_resolution = None
        if resolved_tickets.exists():
            total_hours = 0
            count = 0
            for ticket in resolved_tickets:
                if ticket.resolved_at and ticket.created_at:
                    diff = ticket.resolved_at - ticket.created_at
                    total_hours += diff.total_seconds() / 3600
                    count += 1
            if count > 0:
                avg_resolution = round(total_hours / count, 2)
        
        # Daily trend
        daily_trend = []
        daily_counts = tickets.annotate(date=TruncDate('created_at')).values('date').annotate(count=Count('id')).order_by('date')
        for item in daily_counts:
            daily_trend.append({
                'date': item['date'].isoformat() if item['date'] else None,
                'count': item['count']
            })
        
        # SLA stats
        sla_breached = tickets.filter(sla_breached=True).count()
        sla_met = total_created - sla_breached if total_created > 0 else 0
        
        data = {
            'totalCreated': total_created,
            'totalOpen': total_open,
            'totalClosed': total_closed,
            'averageResolutionTime': avg_resolution,
            'byStatus': by_status,
            'byPriority': by_priority,
            'byCategory': by_category,
            'dailyTrend': daily_trend,
            'slaStats': {
                'met': sla_met,
                'breached': sla_breached,
                'complianceRate': round(sla_met / total_created * 100, 2) if total_created > 0 else 100
            }
        }
        
        return success_response(data)


class AgentPerformanceView(APIView):
    """
    Agent Performance API
    """
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def get(self, request):
        from accounts.models import User
        
        # Get date range from params
        date_from = request.query_params.get('dateFrom')
        date_to = request.query_params.get('dateTo')
        
        # Default to last 30 days
        if not date_to:
            date_to = timezone.now()
        else:
            date_to = timezone.datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        
        if not date_from:
            date_from = date_to - timedelta(days=30)
        else:
            date_from = timezone.datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        
        # Get all support staff, managers, and admins
        staff_users = User.objects.filter(
            role__in=[User.Role.SUPPORT_STAFF, User.Role.MANAGER, User.Role.ADMIN]
        )
        
        performance_data = []
        
        for user in staff_users:
            # Get tickets assigned to this user
            assigned_tickets = Ticket.objects.filter(
                assignee_id=str(user.id),
                created_at__range=[date_from, date_to]
            )
            
            assigned_count = assigned_tickets.count()
            resolved_count = assigned_tickets.filter(status__in=['resolved', 'closed']).count()
            
            # Calculate average resolution time
            resolved_tickets = assigned_tickets.filter(resolved_at__isnull=False)
            avg_resolution = None
            if resolved_tickets.exists():
                total_hours = 0
                count = 0
                for ticket in resolved_tickets:
                    if ticket.resolved_at and ticket.created_at:
                        diff = ticket.resolved_at - ticket.created_at
                        total_hours += diff.total_seconds() / 3600
                        count += 1
                if count > 0:
                    avg_resolution = round(total_hours / count, 2)
            
            # Calculate satisfaction rating
            rated_tickets = assigned_tickets.filter(satisfaction_rating__isnull=False)
            avg_satisfaction = None
            if rated_tickets.exists():
                total_rating = sum(t.satisfaction_rating for t in rated_tickets)
                avg_satisfaction = round(total_rating / rated_tickets.count(), 2)
            
            performance_data.append({
                'agentId': str(user.id),
                'agentName': user.name or user.username,
                'ticketsAssigned': assigned_count,
                'ticketsResolved': resolved_count,
                'averageResolutionTime': avg_resolution,
                'satisfactionRating': avg_satisfaction
            })
        
        return success_response(performance_data)


class KnowledgeAnalyticsView(APIView):
    """
    Knowledge Base Analytics API
    """
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def get(self, request):
        from kb.models import Article
        
        # Get date range from params
        date_from = request.query_params.get('dateFrom')
        date_to = request.query_params.get('dateTo')
        
        # Default to last 30 days
        if not date_to:
            date_to = timezone.now()
        else:
            date_to = timezone.datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        
        if not date_from:
            date_from = date_to - timedelta(days=30)
        else:
            date_from = timezone.datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        
        # Get articles
        articles = Article.objects.all()
        recent_articles = articles.filter(created_at__range=[date_from, date_to])
        
        # Total stats
        total_articles = articles.count()
        total_views = sum(a.views for a in articles)
        total_helpful = sum(a.helpful_count for a in articles)
        
        # By category
        by_category = []
        category_counts = articles.values('category').annotate(count=Count('id'))
        for item in category_counts:
            by_category.append({
                'name': item['category'] or 'Uncategorized',
                'count': item['count']
            })
        
        # Top articles
        top_articles = []
        for article in articles.order_by('-views')[:10]:
            top_articles.append({
                'id': str(article.id),
                'title': article.title,
                'views': article.views,
                'helpfulCount': article.helpful_count
            })
        
        data = {
            'totalArticles': total_articles,
            'totalViews': total_views,
            'totalHelpful': total_helpful,
            'newArticles': recent_articles.count(),
            'byCategory': by_category,
            'topArticles': top_articles
        }
        
        return success_response(data)


class SLAAnalyticsView(APIView):
    """
    SLA Analytics API
    """
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def get(self, request):
        # Get date range from params
        date_from = request.query_params.get('dateFrom')
        date_to = request.query_params.get('dateTo')
        
        # Default to last 30 days
        if not date_to:
            date_to = timezone.now()
        else:
            date_to = timezone.datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        
        if not date_from:
            date_from = date_to - timedelta(days=30)
        else:
            date_from = timezone.datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        
        tickets = Ticket.objects.filter(created_at__range=[date_from, date_to])
        total = tickets.count()
        breached = tickets.filter(sla_breached=True).count()
        met = total - breached
        
        # By priority
        by_priority = {}
        for priority in ['low', 'medium', 'high', 'urgent']:
            priority_tickets = tickets.filter(priority=priority)
            priority_total = priority_tickets.count()
            priority_breached = priority_tickets.filter(sla_breached=True).count()
            by_priority[priority] = {
                'total': priority_total,
                'met': priority_total - priority_breached,
                'breached': priority_breached,
                'complianceRate': round((priority_total - priority_breached) / priority_total * 100, 2) if priority_total > 0 else 100
            }
        
        data = {
            'total': total,
            'met': met,
            'breached': breached,
            'complianceRate': round(met / total * 100, 2) if total > 0 else 100,
            'byPriority': by_priority
        }
        
        return success_response(data)
