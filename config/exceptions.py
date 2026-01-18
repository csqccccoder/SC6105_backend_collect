from rest_framework.views import exception_handler as drf_exception_handler


def api_exception_handler(exc, context):
    """
    Wrap error responses into:
    { "code": <http_status>, "message": <short>, "data": <details or null> }
    """
    response = drf_exception_handler(exc, context)

    if response is None:
        # Unhandled exception -> 500
        return response

    status_code = response.status_code

    # DRF often puts details in response.data
    detail = response.data

    # A simple message; you can refine later
    message = "Error"
    if isinstance(detail, dict) and "detail" in detail:
        message = str(detail["detail"])

    response.data = {
        "code": status_code,
        "message": message,
        "data": detail,
    }
    return response
