预留模板： 
models.py = 数据库里的表结构 + 领域对象
serializers.py = Model ↔ JSON 的转换 + 字段校验
views.py = “这个接口做什么”的业务逻辑
urls.py = URL 路径表，给每个接口一个地址

对于A： 
accounts app ： 
1. accounts/models.py – 用户 & 角色 & 团队 已经有 Django 自带的 User，所以可以在这里补充“扩展信息”和“团队结构”：
这些模型主要是为后面：工单自动分配（Team）、权限控制（Role） 服务。 
2. accounts/serializers.py – 用户信息 & 登录结果
推荐 serializer：
UserSerializer：暴露给前端的基本用户信息：id, username, email, first_name, last_name…
SupportTeamSerializer ：列表/详情用：id, name, type, members（可以只返回成员数量或简要信息）
LoginSerializer： 校验登录请求：比如接收 username, password，做 validate。
将来实现登录接口时，可以用 LoginSerializer 做输入校验，用 UserSerializer 返回用户信息。
3. accounts/views.py – 登录、当前用户、团队管理
和刚才骨架类似：
LoginView(APIView)：
POST /api/accounts/login/
输入：LoginSerializer
输出：登录成功/失败信息（以后可以加 token）
CurrentUserView(APIView)：
GET /api/accounts/me/
输出：当前登录用户信息（UserSerializer）
SupportTeamListCreateView/SupportTeamDetailView：
对应 GET/POST /api/accounts/teams/，GET/PUT/DELETE /api/accounts/teams/{id}/
4. accounts/urls.py – A 的接口入口表

对于C： kb app建议： 
1. kb/models.py 放知识文章，分类，标签
2. kb/serializers.py – 文章的对外形态 & 嵌套字段，这里的 serializer 决定：前端拿到一篇文章时，能看到哪些字段，字段叫什么名。
3. kb/views.py – 文章 CRUD + 搜索
和前面骨架一样：
KnowledgeArticleListCreateView(ListCreateAPIView)
GET /api/kb/articles/ → 列表，支持 query filters（按 category/tag/published）
POST /api/kb/articles/ → 创建文章
KnowledgeArticleDetailView(RetrieveUpdateDestroyAPIView)
GET/PUT/PATCH/DELETE /api/kb/articles/{id}/
KnowledgeSearchView(APIView)
GET /api/kb/search/?q=xxx
4. kb/urls.py – C 的接口入口表
## Backend (Django REST API)

### Prerequisites

- Python 3.10+
- pip
- (Optional) virtualenv

### Setup

1. Create and activate a virtual environment (recommended).
2. Install dependencies
3. .env创建模板：

DEBUG=True
SECRET_KEY=change-me-in-development
ALLOWED_HOSTS=localhost,127.0.0.1

# Optional: PostgreSQL configuration for future deployment
USE_POSTGRES=False
DB_NAME=helpdesk
DB_USER=helpdesk_user
DB_PASSWORD=helpdesk_password
DB_HOST=localhost
DB_PORT=5432 
4.数据库迁移 Django migrations 已经自动生成并应用，`tickets`、`auth` 等都有 migration 文件
python manage.py migrate
5. 启动开发服务器 
python manage.py runserver
'''后端网址为 http://127.0.0.1:8000/ ''' 
根URL会重定向到Swagger UI的网址 /api/docs/ 



