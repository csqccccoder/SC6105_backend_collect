from django.db import models

class KnowledgeArticle(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    # ...