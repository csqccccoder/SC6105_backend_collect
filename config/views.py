# config/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(["GET"])
def ping(request):
    return Response({"ping": "pong"}) 

@api_view(['GET'])
def health_check(request):
    """
    Simple health check endpoint to verify API is running.
    """
    return Response({'status': 'ok'})