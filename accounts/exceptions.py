"""
自定义异常处理器
用于统一错误响应格式
"""
from rest_framework.views import exception_handler
from rest_framework import status
from .response_wrapper import APIResponse


def custom_exception_handler(exc, context):
    """
    自定义异常处理器，返回统一的错误格式
    """
    # 调用 DRF 默认的异常处理器
    response = exception_handler(exc, context)
    
    if response is not None:
        # 根据状态码设置错误消息
        status_code = response.status_code
        
        # 获取错误详情
        if isinstance(response.data, dict):
            if 'detail' in response.data:
                message = response.data['detail']
            elif 'error' in response.data:
                message = response.data['error']
            else:
                # 如果有多个字段错误，合并它们
                errors = []
                for field, error_list in response.data.items():
                    if isinstance(error_list, list):
                        errors.extend(error_list)
                    else:
                        errors.append(str(error_list))
                message = '; '.join(errors) if errors else 'Validation error'
        else:
            message = str(response.data)
        
        # 返回统一格式的错误响应
        return APIResponse(
            data=None,
            message=message,
            code=status_code,
            status_code=status_code
        )
    
    # 如果不是 DRF 识别的异常，返回 500
    return APIResponse(
        data=None,
        message='Internal server error',
        code=500,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
