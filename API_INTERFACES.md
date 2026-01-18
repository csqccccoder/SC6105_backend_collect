# API Interfaces Documentation

## IT Service Ticketing and Knowledge Base Platform - Frontend API Specification

This document lists all API endpoints that the frontend application expects from the backend server.

---

## Base Configuration

```
Base URL: /api
Content-Type: application/json
Authentication: Bearer Token (JWT)
```

---

## 1. Authentication APIs

### 1.1 Login
```
POST /api/auth/login
```

**Request Body:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "token": "string",
    "user": {
      "id": "string",
      "email": "string",
      "name": "string",
      "role": "end_user | support_staff | manager | admin",
      "avatar": "string | null",
      "department": "string | null",
      "phone": "string | null",
      "isActive": "boolean",
      "createdAt": "ISO8601 string"
    }
  }
}
```

### 1.2 SSO Login
```
POST /api/auth/sso
```

**Request Body:**
```json
{
  "ssoToken": "string"
}
```

**Response:** Same as Login

### 1.3 Logout
```
POST /api/auth/logout
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "code": 200,
  "message": "Logged out successfully",
  "data": null
}
```

### 1.4 Get Current User
```
GET /api/auth/me
```

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "id": "string",
    "email": "string",
    "name": "string",
    "role": "string",
    "avatar": "string | null",
    "department": "string | null",
    "phone": "string | null",
    "isActive": "boolean",
    "createdAt": "ISO8601 string"
  }
}
```

---

## 2. User Management APIs

### 2.1 Get Users (Admin)
```
GET /api/users
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | number | Yes | Page number (1-based) |
| pageSize | number | Yes | Items per page |
| keyword | string | No | Search by name or email |
| role | string | No | Filter by role |

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "items": [User],
    "page": "number",
    "pageSize": "number",
    "total": "number",
    "totalPages": "number"
  }
}
```

### 2.2 Get User by ID
```
GET /api/users/:id
```

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "id": "string",
    "email": "string",
    "name": "string",
    "role": "string",
    "avatar": "string | null",
    "department": "string | null",
    "phone": "string | null",
    "isActive": "boolean",
    "createdAt": "ISO8601 string"
  }
}
```

### 2.3 Create User
```
POST /api/users
```

**Request Body:**
```json
{
  "email": "string",
  "name": "string",
  "role": "end_user | support_staff | manager | admin",
  "department": "string (optional)",
  "phone": "string (optional)"
}
```

### 2.4 Update User
```
PUT /api/users/:id
```

**Request Body:**
```json
{
  "name": "string (optional)",
  "role": "string (optional)",
  "department": "string (optional)",
  "phone": "string (optional)",
  "isActive": "boolean (optional)"
}
```

### 2.5 Delete User
```
DELETE /api/users/:id
```

---

## 3. Ticket Management APIs

### 3.1 Get Tickets (Paginated)
```
GET /api/tickets
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | number | Yes | Page number |
| pageSize | number | Yes | Items per page |
| status | string | No | Filter by status |
| priority | string | No | Filter by priority |
| categoryId | string | No | Filter by category |
| assigneeId | string | No | Filter by assignee |
| requesterId | string | No | Filter by requester |
| keyword | string | No | Search in title/description |

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "items": [Ticket],
    "page": "number",
    "pageSize": "number",
    "total": "number",
    "totalPages": "number"
  }
}
```

### 3.2 Get Ticket by ID
```
GET /api/tickets/:id
```

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "id": "string",
    "title": "string",
    "description": "string",
    "status": "new | assigned | in_progress | pending_user | resolved | closed",
    "priority": "low | medium | high | urgent",
    "category": {
      "id": "string",
      "name": "string",
      "description": "string",
      "parentId": "string | null"
    },
    "channel": "web | email | phone | mobile",
    "requesterId": "string",
    "requesterName": "string",
    "requesterEmail": "string",
    "assigneeId": "string | null",
    "assigneeName": "string | null",
    "teamId": "string | null",
    "teamName": "string | null",
    "attachments": [Attachment],
    "comments": [Comment],
    "statusHistory": [StatusHistory],
    "slaResponseDeadline": "ISO8601 string | null",
    "slaResolutionDeadline": "ISO8601 string | null",
    "slaBreached": "boolean",
    "satisfactionRating": "number | null",
    "satisfactionComment": "string | null",
    "createdAt": "ISO8601 string",
    "updatedAt": "ISO8601 string",
    "resolvedAt": "ISO8601 string | null",
    "closedAt": "ISO8601 string | null"
  }
}
```

### 3.3 Create Ticket
```
POST /api/tickets
```

**Request Body:**
```json
{
  "title": "string",
  "description": "string",
  "categoryId": "string",
  "priority": "low | medium | high | urgent",
  "attachments": ["File objects (optional)"]
}
```

### 3.4 Update Ticket
```
PUT /api/tickets/:id
```

**Request Body:**
```json
{
  "title": "string (optional)",
  "description": "string (optional)",
  "status": "string (optional)",
  "priority": "string (optional)",
  "categoryId": "string (optional)",
  "assigneeId": "string (optional)",
  "teamId": "string (optional)"
}
```

### 3.5 Assign Ticket
```
POST /api/tickets/:id/assign
```

**Request Body:**
```json
{
  "assigneeId": "string",
  "teamId": "string (optional)"
}
```

### 3.6 Change Ticket Status
```
POST /api/tickets/:id/status
```

**Request Body:**
```json
{
  "status": "new | assigned | in_progress | pending_user | resolved | closed",
  "comment": "string (optional)"
}
```

### 3.7 Add Comment to Ticket
```
POST /api/tickets/:id/comments
```

**Request Body:**
```json
{
  "content": "string",
  "isInternal": "boolean"
}
```

### 3.8 Submit Satisfaction Rating
```
POST /api/tickets/:id/satisfaction
```

**Request Body:**
```json
{
  "rating": "number (1-5)",
  "comment": "string (optional)"
}
```

### 3.9 Get Ticket Categories
```
GET /api/tickets/categories
```

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "parentId": "string | null"
    }
  ]
}
```

---

## 4. Knowledge Base APIs

### 4.1 Get Published Articles (Public)
```
GET /api/knowledge/articles
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | number | Yes | Page number |
| pageSize | number | Yes | Items per page |
| keyword | string | No | Search in title/content |
| category | string | No | Filter by category |
| tag | string | No | Filter by tag |

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "items": [KnowledgeArticle],
    "page": "number",
    "pageSize": "number",
    "total": "number",
    "totalPages": "number"
  }
}
```

### 4.2 Get All Articles (Staff/Admin)
```
GET /api/knowledge/articles/all
```

Same query parameters as above, includes draft and archived articles.

### 4.3 Get Article by ID
```
GET /api/knowledge/articles/:id
```

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "id": "string",
    "title": "string",
    "content": "string (Markdown)",
    "summary": "string | null",
    "category": "string",
    "tags": ["string"],
    "status": "draft | published | archived",
    "accessLevel": "public | internal",
    "isFAQ": "boolean",
    "authorId": "string",
    "authorName": "string",
    "viewCount": "number",
    "helpfulCount": "number",
    "notHelpfulCount": "number",
    "createdAt": "ISO8601 string",
    "updatedAt": "ISO8601 string",
    "publishedAt": "ISO8601 string | null"
  }
}
```

### 4.4 Create Article
```
POST /api/knowledge/articles
```

**Request Body:**
```json
{
  "title": "string",
  "content": "string (Markdown)",
  "summary": "string (optional)",
  "category": "string",
  "tags": ["string"],
  "accessLevel": "public | internal",
  "isFAQ": "boolean"
}
```

### 4.5 Update Article
```
PUT /api/knowledge/articles/:id
```

**Request Body:** Same as Create

### 4.6 Delete Article
```
DELETE /api/knowledge/articles/:id
```

### 4.7 Publish Article
```
POST /api/knowledge/articles/:id/publish
```

### 4.8 Archive Article
```
POST /api/knowledge/articles/:id/archive
```

### 4.9 Get FAQ Articles
```
GET /api/knowledge/faq
```

**Response:** Array of FAQ articles

### 4.10 Get Suggested Articles
```
GET /api/knowledge/suggestions
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | string | Yes | Search query for suggestions |

### 4.11 Submit Article Feedback
```
POST /api/knowledge/articles/:id/feedback
```

**Request Body:**
```json
{
  "helpful": "boolean"
}
```

### 4.12 Get KB Categories
```
GET /api/knowledge/categories
```

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": ["string"]
}
```

### 4.13 Get Tags
```
GET /api/knowledge/tags
```

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": ["string"]
}
```

---

## 5. Team Management APIs

### 5.1 Get Teams
```
GET /api/teams
```

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": [
    {
      "id": "string",
      "name": "string",
      "description": "string | null",
      "leaderId": "string",
      "leaderName": "string",
      "members": [TeamMember],
      "memberCount": "number",
      "activeTickets": "number",
      "createdAt": "ISO8601 string"
    }
  ]
}
```

### 5.2 Get Team by ID
```
GET /api/teams/:id
```

### 5.3 Create Team
```
POST /api/teams
```

**Request Body:**
```json
{
  "name": "string",
  "description": "string (optional)"
}
```

### 5.4 Update Team
```
PUT /api/teams/:id
```

### 5.5 Delete Team
```
DELETE /api/teams/:id
```

### 5.6 Add Team Member
```
POST /api/teams/:id/members
```

**Request Body:**
```json
{
  "userId": "string",
  "role": "leader | member"
}
```

### 5.7 Remove Team Member
```
DELETE /api/teams/:id/members/:userId
```

---

## 6. Analytics APIs (Manager/Admin)

### 6.1 Get Ticket Analytics
```
GET /api/analytics/tickets
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| period | string | No | Time period (7d, 30d, 90d, 1y) |

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "totalCreated": "number",
    "totalClosed": "number",
    "totalOpen": "number",
    "byPriority": {
      "low": "number",
      "medium": "number",
      "high": "number",
      "urgent": "number"
    },
    "byCategory": [
      { "category": "string", "count": "number" }
    ],
    "byStatus": {
      "new": "number",
      "assigned": "number",
      "in_progress": "number",
      "pending_user": "number",
      "resolved": "number",
      "closed": "number"
    },
    "byChannel": {
      "web": "number",
      "email": "number",
      "phone": "number",
      "mobile": "number"
    },
    "averageResponseTime": "number (minutes)",
    "averageResolutionTime": "number (minutes)",
    "slaComplianceRate": "number (percentage)"
  }
}
```

### 6.2 Get Agent Performance
```
GET /api/analytics/agents
```

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": [
    {
      "agentId": "string",
      "agentName": "string",
      "teamName": "string",
      "resolvedTickets": "number",
      "averageResponseTime": "number",
      "averageResolutionTime": "number",
      "satisfactionScore": "number"
    }
  ]
}
```

### 6.3 Get Knowledge Analytics
```
GET /api/analytics/knowledge
```

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "totalArticles": "number",
    "totalViews": "number",
    "topViewedArticles": [
      { "articleId": "string", "title": "string", "viewCount": "number" }
    ],
    "helpfulRatio": "number",
    "emptySearchQueries": ["string"]
  }
}
```

---

## 7. SLA Configuration APIs (Admin)

### 7.1 Get SLA Configurations
```
GET /api/sla
```

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": [
    {
      "id": "string",
      "priority": "low | medium | high | urgent",
      "responseTimeMinutes": "number",
      "resolutionTimeMinutes": "number",
      "isActive": "boolean"
    }
  ]
}
```

### 7.2 Update SLA Configuration
```
PUT /api/sla/:id
```

**Request Body:**
```json
{
  "responseTimeMinutes": "number",
  "resolutionTimeMinutes": "number",
  "isActive": "boolean"
}
```

---

## 8. Audit Log APIs (Admin)

### 8.1 Get Audit Logs
```
GET /api/audit-logs
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | number | Yes | Page number |
| pageSize | number | Yes | Items per page |
| userId | string | No | Filter by user |
| action | string | No | Filter by action type |
| startDate | string | No | Filter from date |
| endDate | string | No | Filter to date |

**Response:**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "items": [
      {
        "id": "string",
        "userId": "string",
        "userEmail": "string",
        "action": "string",
        "details": "string",
        "ipAddress": "string",
        "timestamp": "ISO8601 string"
      }
    ],
    "page": "number",
    "pageSize": "number",
    "total": "number",
    "totalPages": "number"
  }
}
```

---

## Error Response Format

All error responses follow this format:

```json
{
  "code": "number (HTTP status code)",
  "message": "string (error message)",
  "data": null
}
```

Common error codes:
- 400: Bad Request - Invalid input data
- 401: Unauthorized - Authentication required
- 403: Forbidden - Insufficient permissions
- 404: Not Found - Resource not found
- 500: Internal Server Error

---

## Data Types Reference

### User
```typescript
interface User {
  id: string
  email: string
  name: string
  role: 'end_user' | 'support_staff' | 'manager' | 'admin'
  avatar?: string
  department?: string
  phone?: string
  isActive: boolean
  createdAt: string
}
```

### Ticket
```typescript
interface Ticket {
  id: string
  title: string
  description: string
  status: 'new' | 'assigned' | 'in_progress' | 'pending_user' | 'resolved' | 'closed'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  category: TicketCategory
  channel: 'web' | 'email' | 'phone' | 'mobile'
  requesterId: string
  requesterName: string
  requesterEmail: string
  assigneeId?: string
  assigneeName?: string
  teamId?: string
  teamName?: string
  attachments: Attachment[]
  comments: Comment[]
  statusHistory: StatusHistory[]
  slaResponseDeadline?: string
  slaResolutionDeadline?: string
  slaBreached: boolean
  satisfactionRating?: number
  satisfactionComment?: string
  createdAt: string
  updatedAt: string
  resolvedAt?: string
  closedAt?: string
}
```

### KnowledgeArticle
```typescript
interface KnowledgeArticle {
  id: string
  title: string
  content: string
  summary?: string
  category: string
  tags: string[]
  status: 'draft' | 'published' | 'archived'
  accessLevel: 'public' | 'internal'
  isFAQ: boolean
  authorId: string
  authorName: string
  viewCount: number
  helpfulCount: number
  notHelpfulCount: number
  createdAt: string
  updatedAt: string
  publishedAt?: string
}
```

### Team
```typescript
interface Team {
  id: string
  name: string
  description?: string
  leaderId: string
  leaderName: string
  members: TeamMember[]
  memberCount: number
  activeTickets: number
  createdAt: string
}

interface TeamMember {
  id: string
  userId: string
  userName: string
  userEmail: string
  role: 'leader' | 'member'
  joinedAt: string
}
```

---

## Summary

| Category | Endpoint Count |
|----------|---------------|
| Authentication | 4 |
| User Management | 5 |
| Ticket Management | 9 |
| Knowledge Base | 13 |
| Team Management | 7 |
| Analytics | 3 |
| SLA Configuration | 2 |
| Audit Logs | 1 |
| **Total** | **44** |
