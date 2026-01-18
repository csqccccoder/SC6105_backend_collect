# kb/views.py 填你自己的
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import KnowledgeArticle
from .serializers import KnowledgeArticleSerializer

class KnowledgeArticleListCreateView(generics.ListCreateAPIView):
    queryset = KnowledgeArticle.objects.all()
    serializer_class = KnowledgeArticleSerializer


class KnowledgeArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = KnowledgeArticle.objects.all()
    serializer_class = KnowledgeArticleSerializer


class KnowledgeSearchView(APIView):
    def get(self, request, *args, **kwargs):
        # TODO: simple search by query param q
        q = request.query_params.get("q", "")
        return Response({"results": [], "query": q})
