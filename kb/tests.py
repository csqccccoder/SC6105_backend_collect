from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import KnowledgeArticle, Tag

User = get_user_model()


class KnowledgeBaseTestCase(APITestCase):
    """Test case for Knowledge Base API"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.end_user = User.objects.create_user(
            username='enduser',
            email='enduser@test.com',
            password='testpass123'
        )
        # Set end_user role if role field exists
        if hasattr(self.end_user, 'role'):
            self.end_user.role = 'end_user'
            self.end_user.save()
        
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@test.com',
            password='testpass123',
            is_staff=True
        )
        # Set staff role if role field exists
        if hasattr(self.staff_user, 'role'):
            self.staff_user.role = 'staff'
            self.staff_user.save()
        
        # Create tags
        self.tag1 = Tag.objects.create(name='Python')
        self.tag2 = Tag.objects.create(name='Django')
        
        # Create articles
        self.public_published = KnowledgeArticle.objects.create(
            title='Public Published Article',
            content='This is public content',
            summary='Public summary',
            category='Tutorial',
            status='published',
            access_level='public',
            is_faq=False,
            created_by=self.staff_user
        )
        self.public_published.tags.add(self.tag1)
        
        self.internal_published = KnowledgeArticle.objects.create(
            title='Internal Published Article',
            content='This is internal content',
            summary='Internal summary',
            category='Guide',
            status='published',
            access_level='internal',
            created_by=self.staff_user
        )
        self.internal_published.tags.add(self.tag2)
        
        self.draft_article = KnowledgeArticle.objects.create(
            title='Draft Article',
            content='This is draft content',
            summary='Draft summary',
            category='Tutorial',
            status='draft',
            access_level='public',
            created_by=self.staff_user
        )
        
        self.archived_article = KnowledgeArticle.objects.create(
            title='Archived Article',
            content='This is archived content',
            summary='Archived summary',
            category='Guide',
            status='archived',
            access_level='public',
            created_by=self.staff_user
        )
        
        self.faq_article = KnowledgeArticle.objects.create(
            title='FAQ Article',
            content='This is FAQ content',
            summary='FAQ summary',
            category='FAQ',
            status='published',
            access_level='public',
            is_faq=True,
            created_by=self.staff_user
        )
        
        # Set up API client
        self.client = APIClient()
    
    def get_jwt_token(self, user):
        """Get JWT token for user"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_end_user_cannot_see_internal_articles(self):
        """Test 1: End user cannot see internal articles"""
        token = self.get_jwt_token(self.end_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/knowledge/articles')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response format: {code, message, data}
        self.assertIn('code', response.data)
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        
        # Should only see public published articles
        items = response.data['data']['items']
        titles = [item['title'] for item in items]
        
        self.assertIn('Public Published Article', titles)
        self.assertNotIn('Internal Published Article', titles)
        self.assertNotIn('Draft Article', titles)
        self.assertNotIn('Archived Article', titles)
        
        # Verify camelCase field names in response
        if len(items) > 0:
            item = items[0]
            self.assertIn('authorId', item)
            self.assertIn('authorName', item)
            self.assertIn('viewCount', item)
            self.assertIn('helpfulCount', item)
            self.assertIn('notHelpfulCount', item)
            self.assertIn('accessLevel', item)
            self.assertIn('isFAQ', item)
            self.assertIn('createdAt', item)
            self.assertIn('updatedAt', item)
            # Should NOT contain snake_case fields
            self.assertNotIn('author_id', item)
            self.assertNotIn('view_count', item)
            self.assertNotIn('access_level', item)
            self.assertNotIn('is_faq', item)
    
    def test_end_user_list_faq_suggestions_no_draft_internal(self):
        """Test 2: End user list/suggestions/faq don't show draft/archived/internal"""
        token = self.get_jwt_token(self.end_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Test list
        response = self.client.get('/api/knowledge/articles')
        items = response.data['data']['items']
        statuses = [item['status'] for item in items]
        access_levels = [item['accessLevel'] for item in items]
        
        self.assertTrue(all(s == 'published' for s in statuses))
        self.assertTrue(all(a == 'public' for a in access_levels))
        
        # Test FAQ
        response = self.client.get('/api/knowledge/faq')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        faq_data = response.data['data']
        self.assertTrue(all(item['isFAQ'] for item in faq_data))
        
        # Test suggestions
        response = self.client.get('/api/knowledge/suggestions?query=Article')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        suggestions_data = response.data['data']
        for item in suggestions_data:
            self.assertEqual(item['status'], 'published')
            self.assertEqual(item['accessLevel'], 'public')
    
    def test_staff_can_create_draft(self):
        """Test 3: Staff can create draft articles"""
        token = self.get_jwt_token(self.staff_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'title': 'New Draft Article',
            'content': 'This is new content',
            'summary': 'New summary',
            'category': 'Tutorial',
            'tags': ['Python', 'Testing'],
            'accessLevel': 'public',
            'isFAQ': False
        }
        
        response = self.client.post('/api/knowledge/articles', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        article_data = response.data['data']
        self.assertEqual(article_data['status'], 'draft')
        self.assertEqual(article_data['title'], 'New Draft Article')
        # Verify camelCase fields
        self.assertIn('accessLevel', article_data)
        self.assertIn('isFAQ', article_data)
    
    def test_publish_makes_article_visible_to_end_user(self):
        """Test 4: Publish makes article visible to end user (if public)"""
        # First verify end user can't see draft
        token = self.get_jwt_token(self.end_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/knowledge/articles')
        titles = [item['title'] for item in response.data['data']['items']]
        self.assertNotIn('Draft Article', titles)
        
        # Staff publishes the draft
        token = self.get_jwt_token(self.staff_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.post(f'/api/knowledge/articles/{self.draft_article.id}/publish')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['status'], 'published')
        
        # Now end user can see it
        token = self.get_jwt_token(self.end_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/knowledge/articles')
        titles = [item['title'] for item in response.data['data']['items']]
        self.assertIn('Draft Article', titles)
    
    def test_feedback_helpful_not_helpful_count(self):
        """Test 5: Feedback helpful/notHelpful count is correct"""
        token = self.get_jwt_token(self.end_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        article_id = self.public_published.id
        
        # Get initial counts
        response = self.client.get(f'/api/knowledge/articles/{article_id}')
        article_data = response.data['data']
        initial_helpful = article_data['helpfulCount']
        initial_not_helpful = article_data['notHelpfulCount']
        
        # Submit helpful feedback
        response = self.client.post(
            f'/api/knowledge/articles/{article_id}/feedback',
            {'helpful': True},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check count increased
        response = self.client.get(f'/api/knowledge/articles/{article_id}')
        article_data = response.data['data']
        self.assertEqual(article_data['helpfulCount'], initial_helpful + 1)
        
        # Submit not helpful feedback
        response = self.client.post(
            f'/api/knowledge/articles/{article_id}/feedback',
            {'helpful': False},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check count increased
        response = self.client.get(f'/api/knowledge/articles/{article_id}')
        article_data = response.data['data']
        self.assertEqual(article_data['notHelpfulCount'], initial_not_helpful + 1)
    
    def test_articles_pagination_correct(self):
        """Test 6: /articles pagination total/totalPages correct"""
        token = self.get_jwt_token(self.staff_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Create more articles
        for i in range(15):
            KnowledgeArticle.objects.create(
                title=f'Test Article {i}',
                content=f'Content {i}',
                category='Test',
                status='published',
                access_level='public',
                created_by=self.staff_user
            )
        
        # Test pagination
        response = self.client.get('/api/knowledge/articles?page=1&pageSize=10')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data['data']
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['pageSize'], 10)
        self.assertTrue(data['total'] >= 15)
        self.assertTrue(data['totalPages'] >= 2)
        self.assertEqual(len(data['items']), 10)
    
    def test_tag_category_filter_correct(self):
        """Test 7: Tag/category filter works correctly"""
        token = self.get_jwt_token(self.staff_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Filter by category
        response = self.client.get('/api/knowledge/articles?category=Tutorial')
        items = response.data['data']['items']
        self.assertTrue(all(item['category'] == 'Tutorial' for item in items))
        
        # Filter by tag
        response = self.client.get('/api/knowledge/articles?tag=Python')
        items = response.data['data']['items']
        # Check that all returned articles have the Python tag
        for item in items:
            self.assertIn('Python', item['tags'])
    
    def test_delete_article_not_in_list(self):
        """Test 8: DELETE makes article invisible in list (soft delete)"""
        token = self.get_jwt_token(self.staff_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        article_id = self.public_published.id
        
        # Verify article is visible
        response = self.client.get('/api/knowledge/articles')
        titles = [item['title'] for item in response.data['data']['items']]
        self.assertIn('Public Published Article', titles)
        
        # Delete article - should return 200 with deleted flag
        response = self.client.delete(f'/api/knowledge/articles/{article_id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['deleted'])
        
        # Verify article is not visible
        response = self.client.get('/api/knowledge/articles')
        titles = [item['title'] for item in response.data['data']['items']]
        self.assertNotIn('Public Published Article', titles)
        
        # Verify article still exists in database with deleted_at set
        article = KnowledgeArticle.objects.get(id=article_id)
        self.assertIsNotNone(article.deleted_at)
    
    def test_categories_tags_endpoints(self):
        """Test: Categories and tags endpoints return correct data"""
        token = self.get_jwt_token(self.end_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Test categories - should return string[]
        response = self.client.get('/api/knowledge/categories')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        categories = response.data['data']
        self.assertIsInstance(categories, list)
        # End user should only see categories from visible articles
        self.assertIn('Tutorial', categories)
        self.assertIn('FAQ', categories)
        
        # Test tags - should return string[]
        response = self.client.get('/api/knowledge/tags')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tags = response.data['data']
        self.assertIsInstance(tags, list)
        self.assertIn('Python', tags)
        # Verify all items are strings
        for tag in tags:
            self.assertIsInstance(tag, str)
    
    def test_staff_can_access_articles_all(self):
        """Test: Staff can access /articles/all endpoint"""
        token = self.get_jwt_token(self.staff_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/knowledge/articles/all')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Staff should see all articles including drafts and internal
        titles = [item['title'] for item in response.data['data']['items']]
        self.assertIn('Draft Article', titles)
        self.assertIn('Internal Published Article', titles)
    
    def test_end_user_cannot_access_articles_all(self):
        """Test: End user cannot access /articles/all endpoint"""
        token = self.get_jwt_token(self.end_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.get('/api/knowledge/articles/all')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_end_user_cannot_create_article(self):
        """Test: End user cannot create articles"""
        token = self.get_jwt_token(self.end_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        data = {
            'title': 'Unauthorized Article',
            'content': 'This should not be created',
            'category': 'Test'
        }
        
        response = self.client.post('/api/knowledge/articles', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_camelcase_field_names_in_response(self):
        """Test: Verify all responses use camelCase field names"""
        token = self.get_jwt_token(self.staff_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Create a test article
        data = {
            'title': 'CamelCase Test Article',
            'content': 'Test content',
            'summary': 'Test summary',
            'category': 'Test',
            'tags': ['TestTag'],
            'accessLevel': 'public',
            'isFAQ': True
        }
        
        response = self.client.post('/api/knowledge/articles', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        article_data = response.data['data']
        article_id = article_data['id']
        
        # Verify all camelCase fields are present
        required_camel_fields = [
            'id', 'title', 'content', 'summary', 'category', 'tags',
            'status', 'accessLevel', 'isFAQ',
            'authorId', 'authorName',
            'viewCount', 'helpfulCount', 'notHelpfulCount',
            'createdAt', 'updatedAt', 'publishedAt'
        ]
        
        for field in required_camel_fields:
            self.assertIn(field, article_data, f"Field '{field}' not found in response")
        
        # Verify snake_case fields are NOT present
        forbidden_snake_fields = [
            'access_level', 'is_faq', 'author_id', 'author_name',
            'view_count', 'helpful_count', 'not_helpful_count',
            'created_at', 'updated_at', 'published_at'
        ]
        
        for field in forbidden_snake_fields:
            self.assertNotIn(field, article_data, f"Snake_case field '{field}' should not be in response")
        
        # Test list endpoint
        response = self.client.get('/api/knowledge/articles')
        items = response.data['data']['items']
        if len(items) > 0:
            item = items[0]
            # Check some key camelCase fields
            self.assertIn('accessLevel', item)
            self.assertIn('isFAQ', item)
            self.assertIn('authorId', item)
            self.assertIn('viewCount', item)
