"""
自定义响应包装器
用于统一 API 响应格式
"""
from rest_framework.response import Response
from rest_framework import status


class APIResponse(Response):
    """
    自定义响应类，包装成 {code, message, data} 格式
    """
    def __init__(self, data=None, message='Success', code=None, 
                 status_code=status.HTTP_200_OK, **kwargs):
        """
        Args:
            data: 响应数据
            message: 响应消息
            code: 状态码（默认与 HTTP 状态码相同）
            status_code: HTTP 状态码
        """
        if code is None:
            code = status_code
        
        response_data = {
            'code': code,
            'message': message,
            'data': data
        }
        
        super().__init__(data=response_data, status=status_code, **kwargs)


def success_response(data=None, message='Success', code=200):
    """成功响应的快捷方法"""
    return APIResponse(data=data, message=message, code=code, status_code=status.HTTP_200_OK)


def error_response(message='Error', code=400, status_code=None):
    """错误响应的快捷方法"""
    if status_code is None:
        status_code = code
    return APIResponse(data=None, message=message, code=code, status_code=status_code)
