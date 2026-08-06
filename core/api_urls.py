from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

app_name = 'api'

@api_view(['GET'])
def api_root(request):
    return Response({
        'message': 'Edu Point API v1',
        'endpoints': {
            'courses': '/api/courses/',
            'teachers': '/api/teachers/',
        }
    })

urlpatterns = [
    path('', api_root, name='root'),
]
