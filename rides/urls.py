from django.urls import path
from . import auth_views

app_name = 'rides'

urlpatterns = [
    path('test-admin/', auth_views.test_admin_access, name='test_admin_access'),
    path('check-role/', auth_views.check_user_role, name='check_user_role'),
]
