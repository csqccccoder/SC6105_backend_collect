"""
自定义分页类
符合 API 文档要求的分页格式
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    """
    自定义分页类
    返回格式: {items, page, pageSize, total, totalPages}
    """
    page_size_query_param = 'pageSize'
    page_query_param = 'page'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """
        返回符合文档要求的分页格式
        """
        return Response({
            'items': data,
            'page': self.page.number,
            'pageSize': self.page.paginator.per_page,
            'total': self.page.paginator.count,
            'totalPages': self.page.paginator.num_pages
        })
