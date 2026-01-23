# Sample Data Documentation

This document describes all the sample data populated in the database for demonstration purposes.

---

## 1. Users

| Email | Name | Role | Department | Phone | Password |
|-------|------|------|------------|-------|----------|
| admin@ticket.com | System Administrator | Admin | IT Department | 1380001001 | admin123 |
| manager@ticket.com | Zhang Wei | Manager | Customer Service | 1380001002 | manager123 |
| support1@ticket.com | Li Ming | Support Staff | Technical Support | 1380001003 | support123 |
| support2@ticket.com | Wang Fang | Support Staff | Technical Support | 1380001004 | support123 |
| support3@ticket.com | Chen Jie | Support Staff | Customer Service | 1380001005 | support123 |
| user1@example.com | Liu Yang | End User | Sales | 1390001001 | user123 |
| user2@example.com | Zhao Min | End User | Marketing | 1390001002 | user123 |
| user3@example.com | Sun Lei | End User | Finance | 1390001003 | user123 |
| user4@example.com | Zhou Ting | End User | HR | 1390001004 | user123 |
| user5@example.com | Wu Hao | End User | R&D | 1390001005 | user123 |

---

## 2. Teams

| Team Name | Description | Leader |
|-----------|-------------|--------|
| Technical Support Team | Handles technical issues, software bugs, and system problems | Li Ming |
| Customer Service Team | Handles general inquiries, account issues, and billing questions | Wang Fang |
| Network Operations Team | Handles network connectivity and infrastructure issues | Chen Jie |

---

## 3. Ticket Categories

| Category Name | Description |
|---------------|-------------|
| Hardware Issue | Computer, printer, and peripheral device problems |
| Software Issue | Application errors, installation, and configuration |
| Network Problem | Internet, VPN, and connectivity issues |
| Account & Access | Login problems, password resets, and permissions |
| Email Issue | Email delivery, configuration, and spam issues |
| Data Request | Data extraction, reports, and backups |
| New Service Request | Requests for new services or equipment |
| General Inquiry | General questions and consultations |

---

## 4. SLA Configurations

| Priority | Response Time | Resolution Time | Description |
|----------|---------------|-----------------|-------------|
| Urgent | 1 hour | 4 hours | Critical business impact, requires immediate attention |
| High | 4 hours | 8 hours | Significant impact on business operations |
| Medium | 8 hours | 24 hours | Moderate impact, standard priority |
| Low | 24 hours | 72 hours | Minor impact, can be scheduled |

---

## 5. Tickets

### Urgent Priority
| Title | Status | Channel | Category |
|-------|--------|---------|----------|
| Production server down - Critical | In Progress | Phone | Network Problem |
| Database connection failure | Assigned | Web | Software Issue |

### High Priority
| Title | Status | Channel | Category |
|-------|--------|---------|----------|
| VPN connection not working for remote team | In Progress | Email | Network Problem |
| Email server slow response | Pending User | Web | Email Issue |
| Cannot access CRM system | Resolved | Phone | Account & Access |
| Password reset request | Resolved | Phone | Account & Access |
| Backup restoration needed | In Progress | Phone | Data Request |

### Medium Priority
| Title | Status | Channel | Category |
|-------|--------|---------|----------|
| Printer not working in Building A | Assigned | Web | Hardware Issue |
| Request for new laptop | New | Web | New Service Request |
| Software license expired | In Progress | Email | Software Issue |
| Need access to shared drive | Resolved | Web | Account & Access |
| Outlook calendar sync issue | Closed | Web | Email Issue |
| WiFi weak in conference room | New | Web | Network Problem |
| Cannot install required software | In Progress | Web | Software Issue |
| New employee onboarding - IT setup | Assigned | Email | New Service Request |

### Low Priority
| Title | Status | Channel | Category |
|-------|--------|---------|----------|
| Monitor flickering occasionally | New | Web | Hardware Issue |
| Request for standing desk | Assigned | Web | New Service Request |
| How to use new project management tool? | Resolved | Email | General Inquiry |
| Request monthly sales report | Closed | Web | Data Request |
| Keyboard keys sticking | Closed | Web | Hardware Issue |

---

## 6. Knowledge Articles

| Title | Category | Status | Is FAQ |
|-------|----------|--------|--------|
| How to Connect to VPN | Network | Published | Yes |
| Password Reset Guide | Security | Published | Yes |
| Email Configuration for Mobile Devices | Email | Published | No |
| Printer Setup and Troubleshooting | Hardware | Published | No |
| Software Installation Request Process | Software | Published | No |
| WiFi Connectivity Issues FAQ | Network | Published | Yes |
| New Employee IT Onboarding Checklist | Guide | Published | No |
| Data Backup and Recovery Policy | Security | Published | No |

---

## 7. Tags

The following tags are available for knowledge articles:
- VPN
- Email
- Password
- Printer
- Network
- Software
- Hardware
- Security
- FAQ
- Guide

---

## Summary Statistics

| Data Type | Count |
|-----------|-------|
| Users | 12 |
| Teams | 4 |
| Ticket Categories | 17 |
| SLA Configs | 4 |
| Tickets | 26 |
| Ticket Comments | 47 |
| Knowledge Articles | 10 |
| Tags | 12 |

---

## Quick Login Guide

### For Testing Different Roles:

**Admin Access:**
- Email: `admin@ticket.com`
- Password: `admin123`

**Manager Access:**
- Email: `manager@ticket.com`
- Password: `manager123`

**Support Staff Access:**
- Email: `support1@ticket.com`
- Password: `support123`

**End User Access:**
- Email: `user1@example.com`
- Password: `user123`

---

## Notes

1. All passwords are for development/testing purposes only
2. The data is designed to demonstrate various ticket statuses and workflows
3. Ticket creation dates are spread across the last 15 days for realistic analytics
4. Some tickets have satisfaction ratings (4-5 stars) for closed tickets
5. Comments are distributed across tickets to simulate real conversations
