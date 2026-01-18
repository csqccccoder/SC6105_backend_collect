from rest_framework import serializers
from .models import KnowledgeArticle

class KnowledgeArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeArticle
        fields = "__all__"