#!/usr/bin/env python
"""
Populate database with sample data for demonstration purposes.
Run this script from the backend_temp directory:
    python manage.py shell < populate_data.py
Or:
    python populate_data.py
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from accounts.models import User, Team
from tickets.models import (
    Ticket, TicketCategory, TicketComment, TicketStatusHistory, SLAConfig,
    TicketStatus, TicketPriority, TicketChannel
)
from kb.models import KnowledgeArticle, Tag

print("=" * 60)
print("Starting database population...")
print("=" * 60)

# ============================================================
# 1. Create Users
# ============================================================
print("\n[1/7] Creating users...")

users_data = [
    {
        "email": "admin@ticket.com",
        "username": "admin",
        "name": "System Administrator",
        "role": "admin",
        "department": "IT Department",
        "phone": "1380001001",
        "password": "admin123"
    },
    {
        "email": "manager@ticket.com",
        "username": "manager",
        "name": "Zhang Wei",
        "role": "manager",
        "department": "Customer Service",
        "phone": "1380001002",
        "password": "manager123"
    },
    {
        "email": "support1@ticket.com",
        "username": "support1",
        "name": "Li Ming",
        "role": "support_staff",
        "department": "Technical Support",
        "phone": "1380001003",
        "password": "support123"
    },
    {
        "email": "support2@ticket.com",
        "username": "support2",
        "name": "Wang Fang",
        "role": "support_staff",
        "department": "Technical Support",
        "phone": "1380001004",
        "password": "support123"
    },
    {
        "email": "support3@ticket.com",
        "username": "support3",
        "name": "Chen Jie",
        "role": "support_staff",
        "department": "Customer Service",
        "phone": "1380001005",
        "password": "support123"
    },
    {
        "email": "user1@example.com",
        "username": "user1",
        "name": "Liu Yang",
        "role": "end_user",
        "department": "Sales",
        "phone": "1390001001",
        "password": "user123"
    },
    {
        "email": "user2@example.com",
        "username": "user2",
        "name": "Zhao Min",
        "role": "end_user",
        "department": "Marketing",
        "phone": "1390001002",
        "password": "user123"
    },
    {
        "email": "user3@example.com",
        "username": "user3",
        "name": "Sun Lei",
        "role": "end_user",
        "department": "Finance",
        "phone": "1390001003",
        "password": "user123"
    },
    {
        "email": "user4@example.com",
        "username": "user4",
        "name": "Zhou Ting",
        "role": "end_user",
        "department": "HR",
        "phone": "1390001004",
        "password": "user123"
    },
    {
        "email": "user5@example.com",
        "username": "user5",
        "name": "Wu Hao",
        "role": "end_user",
        "department": "R&D",
        "phone": "1390001005",
        "password": "user123"
    },
]

created_users = []
for user_data in users_data:
    try:
        user = User.objects.get(email=user_data["email"])
        print(f"  User exists: {user.name} ({user.email})")
    except User.DoesNotExist:
        try:
            user = User.objects.create(
                email=user_data["email"],
                username=user_data["username"],
                name=user_data["name"],
                role=user_data["role"],
                department=user_data["department"],
                phone=user_data["phone"],
            )
            user.set_password(user_data["password"])
            user.save()
            print(f"  Created user: {user.name} ({user.email})")
        except Exception as e:
            print(f"  Error creating user {user_data['email']}: {e}")
            continue
    created_users.append(user)

admin_user = User.objects.filter(role='admin').first()
manager_user = User.objects.filter(role='manager').first()
support_users = list(User.objects.filter(role='support_staff'))
end_users = list(User.objects.filter(role='end_user'))

# ============================================================
# 2. Create Teams
# ============================================================
print("\n[2/7] Creating teams...")

teams_data = [
    {
        "name": "Technical Support Team",
        "description": "Handles technical issues, software bugs, and system problems",
    },
    {
        "name": "Customer Service Team",
        "description": "Handles general inquiries, account issues, and billing questions",
    },
    {
        "name": "Network Operations Team",
        "description": "Handles network connectivity and infrastructure issues",
    },
]

created_teams = []
for i, team_data in enumerate(teams_data):
    leader = support_users[i] if i < len(support_users) else manager_user
    team, created = Team.objects.get_or_create(
        name=team_data["name"],
        defaults={
            "description": team_data["description"],
            "leader": leader,
        }
    )
    if created:
        print(f"  Created team: {team.name}")
    else:
        print(f"  Team exists: {team.name}")
    created_teams.append(team)

# ============================================================
# 3. Create Ticket Categories
# ============================================================
print("\n[3/7] Creating ticket categories...")

categories_data = [
    {"name": "Hardware Issue", "description": "Computer, printer, and peripheral device problems"},
    {"name": "Software Issue", "description": "Application errors, installation, and configuration"},
    {"name": "Network Problem", "description": "Internet, VPN, and connectivity issues"},
    {"name": "Account & Access", "description": "Login problems, password resets, and permissions"},
    {"name": "Email Issue", "description": "Email delivery, configuration, and spam issues"},
    {"name": "Data Request", "description": "Data extraction, reports, and backups"},
    {"name": "New Service Request", "description": "Requests for new services or equipment"},
    {"name": "General Inquiry", "description": "General questions and consultations"},
]

created_categories = []
for cat_data in categories_data:
    category, created = TicketCategory.objects.get_or_create(
        name=cat_data["name"],
        defaults={"description": cat_data["description"]}
    )
    if created:
        print(f"  Created category: {category.name}")
    else:
        print(f"  Category exists: {category.name}")
    created_categories.append(category)

# ============================================================
# 4. Create SLA Configurations
# ============================================================
print("\n[4/7] Creating SLA configurations...")

sla_data = [
    {"priority": "urgent", "response_time": 1, "resolution_time": 4, "description": "Critical business impact, requires immediate attention"},
    {"priority": "high", "response_time": 4, "resolution_time": 8, "description": "Significant impact on business operations"},
    {"priority": "medium", "response_time": 8, "resolution_time": 24, "description": "Moderate impact, standard priority"},
    {"priority": "low", "response_time": 24, "resolution_time": 72, "description": "Minor impact, can be scheduled"},
]

for sla in sla_data:
    obj, created = SLAConfig.objects.get_or_create(
        priority=sla["priority"],
        defaults={
            "response_time": sla["response_time"],
            "resolution_time": sla["resolution_time"],
            "description": sla["description"],
            "is_active": True,
        }
    )
    if created:
        print(f"  Created SLA: {sla['priority']} - Response: {sla['response_time']}h, Resolution: {sla['resolution_time']}h")
    else:
        print(f"  SLA exists: {sla['priority']}")

# ============================================================
# 5. Create Tickets
# ============================================================
print("\n[5/7] Creating tickets...")

tickets_data = [
    # Urgent tickets
    {
        "title": "Production server down - Critical",
        "description": "The main production server is not responding. All customer-facing services are affected. This is a P1 incident requiring immediate attention.",
        "status": "in_progress",
        "priority": "urgent",
        "category_name": "Network Problem",
        "channel": "phone",
        "days_ago": 0,
    },
    {
        "title": "Database connection failure",
        "description": "Unable to connect to the main database. Multiple applications are reporting connection timeout errors.",
        "status": "assigned",
        "priority": "urgent",
        "category_name": "Software Issue",
        "channel": "web",
        "days_ago": 1,
    },
    # High priority tickets
    {
        "title": "VPN connection not working for remote team",
        "description": "The entire remote development team cannot connect to VPN since this morning. They are unable to access internal resources.",
        "status": "in_progress",
        "priority": "high",
        "category_name": "Network Problem",
        "channel": "email",
        "days_ago": 1,
    },
    {
        "title": "Email server slow response",
        "description": "Emails are taking 10-15 minutes to be delivered. Multiple users have reported this issue.",
        "status": "pending_user",
        "priority": "high",
        "category_name": "Email Issue",
        "channel": "web",
        "days_ago": 2,
    },
    {
        "title": "Cannot access CRM system",
        "description": "Getting 'Access Denied' error when trying to log into the CRM system. Need this urgently for client meetings today.",
        "status": "resolved",
        "priority": "high",
        "category_name": "Account & Access",
        "channel": "phone",
        "days_ago": 3,
    },
    # Medium priority tickets
    {
        "title": "Printer not working in Building A",
        "description": "The shared printer on Floor 2, Building A is showing offline status. Multiple employees cannot print documents.",
        "status": "assigned",
        "priority": "medium",
        "category_name": "Hardware Issue",
        "channel": "web",
        "days_ago": 2,
    },
    {
        "title": "Request for new laptop",
        "description": "My current laptop is 5 years old and running very slowly. Requesting a new laptop for better productivity.",
        "status": "new",
        "priority": "medium",
        "category_name": "New Service Request",
        "channel": "web",
        "days_ago": 4,
    },
    {
        "title": "Software license expired",
        "description": "Adobe Creative Suite license has expired. Need renewal for the design team (5 users).",
        "status": "in_progress",
        "priority": "medium",
        "category_name": "Software Issue",
        "channel": "email",
        "days_ago": 5,
    },
    {
        "title": "Need access to shared drive",
        "description": "I recently joined the marketing team and need access to the Marketing shared drive.",
        "status": "resolved",
        "priority": "medium",
        "category_name": "Account & Access",
        "channel": "web",
        "days_ago": 6,
    },
    {
        "title": "Outlook calendar sync issue",
        "description": "My Outlook calendar is not syncing with my mobile device. I keep missing meetings.",
        "status": "closed",
        "priority": "medium",
        "category_name": "Email Issue",
        "channel": "web",
        "days_ago": 7,
    },
    # Low priority tickets
    {
        "title": "Monitor flickering occasionally",
        "description": "My monitor flickers sometimes, about 2-3 times per day. It's not critical but annoying.",
        "status": "new",
        "priority": "low",
        "category_name": "Hardware Issue",
        "channel": "web",
        "days_ago": 3,
    },
    {
        "title": "Request for standing desk",
        "description": "Would like to request a standing desk for ergonomic reasons.",
        "status": "assigned",
        "priority": "low",
        "category_name": "New Service Request",
        "channel": "web",
        "days_ago": 8,
    },
    {
        "title": "How to use new project management tool?",
        "description": "We recently switched to a new project management tool. Could you provide training or documentation?",
        "status": "resolved",
        "priority": "low",
        "category_name": "General Inquiry",
        "channel": "email",
        "days_ago": 10,
    },
    {
        "title": "Request monthly sales report",
        "description": "Need the monthly sales report for Q4 2025 for the upcoming board meeting.",
        "status": "closed",
        "priority": "low",
        "category_name": "Data Request",
        "channel": "web",
        "days_ago": 12,
    },
    {
        "title": "Keyboard keys sticking",
        "description": "Several keys on my keyboard are sticking. Would like a replacement keyboard.",
        "status": "closed",
        "priority": "low",
        "category_name": "Hardware Issue",
        "channel": "web",
        "days_ago": 15,
    },
    # Additional tickets for variety
    {
        "title": "WiFi weak in conference room",
        "description": "WiFi signal is very weak in Conference Room B. Video calls keep dropping.",
        "status": "new",
        "priority": "medium",
        "category_name": "Network Problem",
        "channel": "web",
        "days_ago": 1,
    },
    {
        "title": "Cannot install required software",
        "description": "Getting 'Administrator privileges required' error when trying to install Python.",
        "status": "in_progress",
        "priority": "medium",
        "category_name": "Software Issue",
        "channel": "web",
        "days_ago": 2,
    },
    {
        "title": "Password reset request",
        "description": "Forgot my password and the self-service reset is not working.",
        "status": "resolved",
        "priority": "high",
        "category_name": "Account & Access",
        "channel": "phone",
        "days_ago": 0,
    },
    {
        "title": "Backup restoration needed",
        "description": "Accidentally deleted important files from the shared drive. Need to restore from backup.",
        "status": "in_progress",
        "priority": "high",
        "category_name": "Data Request",
        "channel": "phone",
        "days_ago": 1,
    },
    {
        "title": "New employee onboarding - IT setup",
        "description": "New employee John Smith starting next Monday. Please prepare laptop, accounts, and access.",
        "status": "assigned",
        "priority": "medium",
        "category_name": "New Service Request",
        "channel": "email",
        "days_ago": 3,
    },
]

created_tickets = []
category_map = {cat.name: cat for cat in created_categories}

for i, ticket_data in enumerate(tickets_data):
    user = end_users[i % len(end_users)]
    support = support_users[i % len(support_users)] if ticket_data["status"] != "new" else None
    team = created_teams[i % len(created_teams)] if ticket_data["status"] != "new" else None
    
    created_time = timezone.now() - timedelta(days=ticket_data["days_ago"], hours=random.randint(0, 23))
    
    ticket = Ticket.objects.create(
        title=ticket_data["title"],
        description=ticket_data["description"],
        status=ticket_data["status"],
        priority=ticket_data["priority"],
        category=category_map[ticket_data["category_name"]],
        channel=ticket_data["channel"],
        requester_id=str(user.id),
        requester_name=user.name,
        requester_email=user.email,
        assignee_id=str(support.id) if support else None,
        assignee_name=support.name if support else None,
        team_id=str(team.id) if team else None,
        team_name=team.name if team else None,
    )
    ticket.created_at = created_time
    ticket.save(update_fields=['created_at'])
    
    # Set resolved/closed timestamps
    if ticket_data["status"] == "resolved":
        ticket.resolved_at = created_time + timedelta(hours=random.randint(2, 24))
        ticket.save(update_fields=['resolved_at'])
    elif ticket_data["status"] == "closed":
        ticket.resolved_at = created_time + timedelta(hours=random.randint(2, 24))
        ticket.closed_at = ticket.resolved_at + timedelta(hours=random.randint(1, 12))
        ticket.satisfaction_rating = random.choice([4, 5, 5, 5])
        ticket.satisfaction_comment = random.choice([
            "Great service, very quick response!",
            "Issue resolved perfectly.",
            "Thank you for the help!",
            "Very professional support.",
            None
        ])
        ticket.save(update_fields=['resolved_at', 'closed_at', 'satisfaction_rating', 'satisfaction_comment'])
    
    created_tickets.append(ticket)
    print(f"  Created ticket: [{ticket_data['priority'].upper()}] {ticket_data['title'][:40]}...")

# ============================================================
# 6. Create Ticket Comments
# ============================================================
print("\n[6/7] Creating ticket comments...")

comments_templates = [
    ("support", "Thank you for reporting this issue. I'm looking into it now."),
    ("user", "Any updates on this?"),
    ("support", "I've identified the root cause. Working on a solution."),
    ("support", "The issue has been resolved. Please verify and let me know if it works."),
    ("user", "Confirmed working. Thank you!"),
    ("support", "I need more information to proceed. Could you provide screenshots?"),
    ("user", "Here are the details you requested."),
    ("support", "This is an internal note: Escalated to Level 2 support.", True),
]

comment_count = 0
for ticket in created_tickets:
    if ticket.status in ["new"]:
        continue
    
    num_comments = random.randint(1, 4)
    support = support_users[random.randint(0, len(support_users)-1)]
    user = end_users[random.randint(0, len(end_users)-1)]
    
    for j in range(num_comments):
        template = comments_templates[j % len(comments_templates)]
        is_internal = len(template) > 2 and template[2] == True
        
        if template[0] == "support":
            author = support
        else:
            author = user
        
        comment = TicketComment.objects.create(
            ticket=ticket,
            content=template[1],
            is_internal=is_internal,
            author_id=str(author.id),
            author_name=author.name,
            author_email=author.email,
        )
        comment_count += 1

print(f"  Created {comment_count} comments")

# ============================================================
# 7. Create Knowledge Articles
# ============================================================
print("\n[7/7] Creating knowledge articles...")

# Create tags first
tags_list = ["VPN", "Email", "Password", "Printer", "Network", "Software", "Hardware", "Security", "FAQ", "Guide"]
created_tags = []
for tag_name in tags_list:
    tag, created = Tag.objects.get_or_create(name=tag_name)
    created_tags.append(tag)

articles_data = [
    {
        "title": "How to Connect to VPN",
        "content": """# How to Connect to VPN

## Prerequisites
- VPN client installed (download from IT portal)
- Valid company credentials

## Steps

### Windows Users
1. Open the VPN client application
2. Enter your company email as username
3. Enter your network password
4. Click "Connect"
5. Wait for the connection to establish

### Mac Users
1. Open System Preferences > Network
2. Select the VPN connection
3. Enter your credentials
4. Click "Connect"

## Troubleshooting
- If connection fails, check your internet connectivity
- Ensure your password hasn't expired
- Contact IT support if issues persist

## FAQ
**Q: Why does my VPN disconnect frequently?**
A: This could be due to unstable internet connection. Try using a wired connection instead of WiFi.
""",
        "category": "Network",
        "tags": ["VPN", "Network", "Guide"],
        "is_faq": True,
        "status": "published",
    },
    {
        "title": "Password Reset Guide",
        "content": """# Password Reset Guide

## Self-Service Password Reset

### If you can access the reset portal:
1. Go to https://password.company.com
2. Click "Forgot Password"
3. Enter your email address
4. Check your email for the reset link
5. Click the link and create a new password

### Password Requirements:
- Minimum 12 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character (!@#$%^&*)

## If Self-Service Doesn't Work
Contact IT Support:
- Phone: 1234-5678
- Email: it-support@company.com
- Create a ticket in the support portal

## Security Tips
- Never share your password
- Don't use the same password for multiple accounts
- Change your password every 90 days
""",
        "category": "Security",
        "tags": ["Password", "Security", "FAQ"],
        "is_faq": True,
        "status": "published",
    },
    {
        "title": "Email Configuration for Mobile Devices",
        "content": """# Email Configuration for Mobile Devices

## iOS (iPhone/iPad)

1. Go to Settings > Mail > Accounts
2. Tap "Add Account"
3. Select "Microsoft Exchange"
4. Enter your email and password
5. Allow the profile to be installed

## Android

1. Open the Gmail app
2. Tap your profile picture > Add another account
3. Select "Exchange"
4. Enter your email and password
5. Follow the prompts

## Common Settings
- Server: mail.company.com
- Port: 443
- Security: SSL/TLS

## Troubleshooting
- Ensure mobile device management (MDM) is approved
- Check if your account is enabled for mobile access
- Verify your password is correct
""",
        "category": "Email",
        "tags": ["Email", "Guide"],
        "is_faq": False,
        "status": "published",
    },
    {
        "title": "Printer Setup and Troubleshooting",
        "content": """# Printer Setup and Troubleshooting

## Adding a Network Printer

### Windows
1. Open Settings > Devices > Printers & scanners
2. Click "Add a printer or scanner"
3. Select the printer from the list
4. Click "Add device"

### If printer is not listed:
1. Click "The printer I want isn't listed"
2. Select "Add a printer using TCP/IP address"
3. Enter the printer IP address

## Common Printer Issues

### Printer shows Offline
1. Check if the printer is powered on
2. Verify network cable is connected
3. Restart the print spooler service
4. Remove and re-add the printer

### Print jobs stuck in queue
1. Open print queue
2. Cancel all documents
3. Restart print spooler
4. Try printing again

## Printer Locations
- Floor 1: HP LaserJet Pro (192.168.1.101)
- Floor 2: Canon ImageRunner (192.168.1.102)
- Floor 3: Xerox WorkCentre (192.168.1.103)
""",
        "category": "Hardware",
        "tags": ["Printer", "Hardware", "Guide"],
        "is_faq": False,
        "status": "published",
    },
    {
        "title": "Software Installation Request Process",
        "content": """# Software Installation Request Process

## Overview
Due to security policies, standard users cannot install software directly. Follow this process to request software installation.

## Steps

1. **Submit a Request**
   - Create a ticket in the IT Support Portal
   - Category: "Software Issue"
   - Include software name and version
   - Provide business justification

2. **Approval Process**
   - Your manager will receive an approval request
   - IT Security will review the software
   - Typical approval time: 2-3 business days

3. **Installation**
   - Once approved, IT will schedule installation
   - You'll receive a calendar invite
   - Installation typically takes 15-30 minutes

## Pre-Approved Software
The following software can be requested without additional approval:
- Microsoft Office Suite
- Adobe Acrobat Reader
- 7-Zip
- Notepad++
- VS Code

## Software Not Allowed
- Unlicensed software
- Games
- P2P file sharing applications
- Unauthorized remote access tools
""",
        "category": "Software",
        "tags": ["Software", "Guide"],
        "is_faq": False,
        "status": "published",
    },
    {
        "title": "WiFi Connectivity Issues FAQ",
        "content": """# WiFi Connectivity Issues FAQ

## Frequently Asked Questions

### Q: How do I connect to the company WiFi?
**A:** 
1. Select "Company-WiFi" from available networks
2. Enter your company email and password
3. Accept the security certificate

### Q: Why is my WiFi slow?
**A:** Common causes:
- Too many devices connected
- Distance from access point
- Interference from other devices
- Network congestion during peak hours

### Q: WiFi keeps disconnecting, what should I do?
**A:**
1. Forget the network and reconnect
2. Restart your device
3. Check if others have the same issue
4. Report to IT if problem persists

### Q: Can I connect personal devices?
**A:** Yes, use "Company-Guest" network for personal devices. Note that access is limited to internet only.

### Q: What's the guest WiFi password?
**A:** Guest WiFi password changes monthly. Check the lobby notice board or ask reception.

## Coverage Areas
All floors have WiFi coverage. If you find a dead spot, please report it to IT.
""",
        "category": "Network",
        "tags": ["Network", "FAQ"],
        "is_faq": True,
        "status": "published",
    },
    {
        "title": "New Employee IT Onboarding Checklist",
        "content": """# New Employee IT Onboarding Checklist

## Before First Day
- [ ] Laptop/Desktop ordered
- [ ] Email account created
- [ ] Access card prepared
- [ ] Software licenses allocated

## First Day Setup
- [ ] Receive equipment from IT
- [ ] Set up email on computer
- [ ] Configure email on mobile (optional)
- [ ] Connect to WiFi
- [ ] Set up VPN access
- [ ] Complete security awareness training

## First Week
- [ ] Request access to required systems
- [ ] Join relevant Teams/Slack channels
- [ ] Set up multi-factor authentication
- [ ] Review IT security policies

## Important Links
- IT Support Portal: support.company.com
- Password Reset: password.company.com
- HR Portal: hr.company.com
- Learning Portal: learn.company.com

## Need Help?
Contact IT Support:
- Email: it-support@company.com
- Phone: 1234-5678
- Hours: Mon-Fri 8:00-18:00
""",
        "category": "Guide",
        "tags": ["Guide", "FAQ"],
        "is_faq": False,
        "status": "published",
    },
    {
        "title": "Data Backup and Recovery Policy",
        "content": """# Data Backup and Recovery Policy

## Overview
This document outlines the company's data backup and recovery procedures.

## What is Backed Up
- Network shared drives (daily)
- Email servers (hourly)
- Database servers (every 6 hours)
- User home directories (daily)

## What is NOT Backed Up
- Local C: drive on laptops/desktops
- Personal devices
- USB drives
- Temporary folders

## Backup Retention
| Type | Retention Period |
|------|------------------|
| Daily | 30 days |
| Weekly | 12 weeks |
| Monthly | 12 months |
| Yearly | 7 years |

## How to Request Data Recovery
1. Create a ticket in IT Support Portal
2. Category: "Data Request"
3. Provide:
   - File/folder path
   - Approximate date of the data you need
   - Reason for recovery

## Recovery Time
- Standard request: 24-48 hours
- Urgent request: 4-8 hours (requires manager approval)

## Best Practices
- Save important files to network drives
- Don't rely solely on local storage
- Regularly clean up unnecessary files
""",
        "category": "Security",
        "tags": ["Security", "Guide"],
        "is_faq": False,
        "status": "published",
    },
]

for article_data in articles_data:
    article, created = KnowledgeArticle.objects.get_or_create(
        title=article_data["title"],
        defaults={
            "content": article_data["content"],
            "category": article_data["category"],
            "status": article_data["status"],
            "is_faq": article_data["is_faq"],
            "access_level": "public",
            "created_by": admin_user,
            "updated_by": admin_user,
            "view_count": random.randint(10, 500),
            "helpful_count": random.randint(5, 100),
            "not_helpful_count": random.randint(0, 10),
            "published_at": timezone.now() - timedelta(days=random.randint(1, 30)),
        }
    )
    
    if created:
        # Add tags
        for tag_name in article_data["tags"]:
            tag = Tag.objects.get(name=tag_name)
            article.tags.add(tag)
        print(f"  Created article: {article.title}")
    else:
        print(f"  Article exists: {article.title}")

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
print("Database population completed!")
print("=" * 60)
print(f"""
Summary:
- Users: {User.objects.count()}
- Teams: {Team.objects.count()}
- Ticket Categories: {TicketCategory.objects.count()}
- SLA Configs: {SLAConfig.objects.count()}
- Tickets: {Ticket.objects.count()}
- Ticket Comments: {TicketComment.objects.count()}
- Knowledge Articles: {KnowledgeArticle.objects.count()}
- Tags: {Tag.objects.count()}

Test Accounts:
+-------------------+---------------------+-------------+
| Role              | Email               | Password    |
+-------------------+---------------------+-------------+
| Admin             | admin@ticket.com    | admin123    |
| Manager           | manager@ticket.com  | manager123  |
| Support Staff     | support1@ticket.com | support123  |
| Support Staff     | support2@ticket.com | support123  |
| Support Staff     | support3@ticket.com | support123  |
| End User          | user1@example.com   | user123     |
| End User          | user2@example.com   | user123     |
+-------------------+---------------------+-------------+
""")
