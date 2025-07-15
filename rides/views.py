from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import User, Ride, RideEvent
from .serializers import (
    UserSerializer, 
    UserCreateSerializer, 
    UserSummarySerializer,
    RideSerializer,
    RideCreateSerializer,
    RideListSerializer,
    RideEventSerializer,
    RideEventCreateSerializer,
    TodaysRideEventSerializer,
)
from .permissions import IsAdminUser, IsAdminUserOrReadOnly


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model with full CRUD operations.
    Only accessible by admin users as per specification.
    """
    
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtering options
    filterset_fields = ['role', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'phone_number']
    ordering_fields = ['id_user', 'first_name', 'last_name', 'email', 'created_at']
    ordering = ['-created_at']  # Default ordering
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'list':
            return UserSummarySerializer
        return UserSerializer
    
    def get_queryset(self):
        """
        Optionally filter users by role or active status.
        """
        queryset = User.objects.all()
        
        # Filter by role if specified
        role = self.request.query_params.get('role', None)
        if role and role in ['admin', 'driver', 'rider']:
            queryset = queryset.filter(role=role)
        
        # Filter by active status if specified
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_active=is_active_bool)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Create a new user with proper validation.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Return full user data using UserSerializer
        response_serializer = UserSerializer(user)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """
        Update user with partial update support.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response(UserSerializer(user).data)
    
    def destroy(self, request, *args, **kwargs):
        """
        Soft delete user by setting is_active to False.
        """
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        
        return Response(
            {'message': f'User {instance.email} has been deactivated successfully.'}, 
            status=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Reactivate a deactivated user.
        """
        user = self.get_object()
        user.is_active = True
        user.save()
        
        return Response(
            {'message': f'User {user.email} has been activated successfully.'}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def drivers(self, request):
        """
        Get all users with driver role.
        """
        drivers = User.objects.filter(role='driver', is_active=True)
        serializer = UserSummarySerializer(drivers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def riders(self, request):
        """
        Get all users with rider role.
        """
        riders = User.objects.filter(role='rider', is_active=True)
        serializer = UserSummarySerializer(riders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def rides(self, request, pk=None):
        """
        Get all rides for a specific user (as rider or driver).
        """
        user = self.get_object()
        rides = Ride.objects.filter(
            Q(id_rider=user) | Q(id_driver=user)
        ).order_by('-created_at')
        
        serializer = RideListSerializer(rides, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get user statistics.
        """
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        drivers = User.objects.filter(role='driver', is_active=True).count()
        riders = User.objects.filter(role='rider', is_active=True).count()
        admins = User.objects.filter(role='admin', is_active=True).count()
        
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'drivers': drivers,
            'riders': riders,
            'admins': admins,
            'inactive_users': total_users - active_users,
        })
