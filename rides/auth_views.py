from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .permissions import IsAdminUser


@api_view(['GET'])
@permission_classes([IsAdminUser])
def test_admin_access(request):
    """
    Test endpoint to verify admin-only authentication is working.
    Only users with 'admin' role should be able to access this.
    """
    return Response({
        'message': 'Admin access confirmed!',
        'user': {
            'email': request.user.email,
            'role': request.user.role,
            'full_name': request.user.full_name,
        }
    })


@api_view(['GET'])
def check_user_role(request):
    """
    Endpoint to check current user's role and authentication status.
    Useful for debugging authentication issues.
    """
    if not request.user.is_authenticated:
        return Response({
            'authenticated': False,
            'message': 'User is not authenticated'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response({
        'authenticated': True,
        'user': {
            'email': request.user.email,
            'role': request.user.role,
            'is_admin': request.user.is_admin(),
            'full_name': request.user.full_name,
        }
    })
