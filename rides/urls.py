from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from . import views, auth_views

app_name = 'rides'

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'rides', views.RideViewSet, basename='ride')
router.register(r'ride-events', views.RideEventViewSet, basename='rideevent')


urlpatterns = [
    # RESTful API endpoints via router
    path('', include(router.urls)),

    # Authentication
    path('auth/token/', obtain_auth_token, name='api_token_auth'),

    # Legacy test endpoints (backward compatibility)
    path('test-admin/', auth_views.test_admin_access, name='test_admin_access'),
    path('check-role/', auth_views.check_user_role, name='check_user_role'),
]

# API Documentation: Visit /api/api/ for interactive API browser
# Or see README.md for complete endpoint documentation
