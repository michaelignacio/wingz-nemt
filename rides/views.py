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


class RideEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for RideEvent model with CRUD operations.
    Includes performance optimizations for large datasets.
    Only accessible by admin users as per specification.
    """
    
    queryset = RideEvent.objects.select_related('id_ride', 'id_ride__id_rider', 'id_ride__id_driver').all()
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtering options
    filterset_fields = ['event_type', 'id_ride', 'id_ride__status']
    search_fields = ['event_type', 'id_ride__id_rider__email', 'id_ride__id_driver__email']
    ordering_fields = ['id_ride_event', 'event_time', 'event_type', 'created_at']
    ordering = ['-event_time']  # Default ordering by most recent events
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return RideEventCreateSerializer
        elif self.action == 'todays_events':
            return TodaysRideEventSerializer
        return RideEventSerializer
    
    def get_queryset(self):
        """
        Optimized queryset with filtering options.
        """
        queryset = RideEvent.objects.select_related(
            'id_ride', 
            'id_ride__id_rider', 
            'id_ride__id_driver'
        ).all()
        
        # Filter by ride ID if specified
        ride_id = self.request.query_params.get('ride_id', None)
        if ride_id:
            queryset = queryset.filter(id_ride=ride_id)
        
        # Filter by event type if specified
        event_type = self.request.query_params.get('event_type', None)
        if event_type:
            queryset = queryset.filter(event_type__icontains=event_type)
        
        # Filter by date range if specified
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            try:
                from datetime import datetime
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                queryset = queryset.filter(event_time__gte=start_datetime)
            except ValueError:
                pass  # Invalid date format, ignore filter
        
        if end_date:
            try:
                from datetime import datetime
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                queryset = queryset.filter(event_time__lte=end_datetime)
            except ValueError:
                pass  # Invalid date format, ignore filter
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Create a new ride event with proper validation.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ride_event = serializer.save()
        
        # Return full ride event data using RideEventSerializer
        response_serializer = RideEventSerializer(ride_event)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """
        Update ride event with partial update support.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        ride_event = serializer.save()
        
        return Response(RideEventSerializer(ride_event).data)
    
    @action(detail=False, methods=['get'])
    def todays_events(self, request):
        """
        Get all ride events from today with performance optimization.
        This is the optimized endpoint mentioned in the specification.
        """
        from datetime import datetime, timezone, timedelta
        
        # Get events from the last 24 hours
        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        
        todays_events = self.get_queryset().filter(
            event_time__gte=twenty_four_hours_ago
        ).order_by('-event_time')
        
        # Apply pagination for performance
        page = self.paginate_queryset(todays_events)
        if page is not None:
            serializer = TodaysRideEventSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TodaysRideEventSerializer(todays_events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_ride(self, request):
        """
        Get all events for a specific ride.
        """
        ride_id = request.query_params.get('ride_id')
        if not ride_id:
            return Response(
                {'error': 'ride_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            ride = Ride.objects.get(id_ride=ride_id)
        except Ride.DoesNotExist:
            return Response(
                {'error': 'Ride not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        events = self.get_queryset().filter(id_ride=ride).order_by('event_time')
        serializer = RideEventSerializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def event_types(self, request):
        """
        Get all unique event types in the system.
        """
        event_types = RideEvent.objects.values_list(
            'event_type', flat=True
        ).distinct().order_by('event_type')
        
        return Response({
            'event_types': list(event_types),
            'count': len(event_types)
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get ride event statistics.
        """
        from datetime import datetime, timezone, timedelta
        
        total_events = RideEvent.objects.count()
        
        # Events from last 24 hours
        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        todays_events = RideEvent.objects.filter(event_time__gte=twenty_four_hours_ago).count()
        
        # Events from last 7 days
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        weekly_events = RideEvent.objects.filter(event_time__gte=seven_days_ago).count()
        
        # Most common event types
        from django.db.models import Count
        common_event_types = RideEvent.objects.values('event_type').annotate(
            count=Count('event_type')
        ).order_by('-count')[:5]
        
        return Response({
            'total_events': total_events,
            'todays_events': todays_events,
            'weekly_events': weekly_events,
            'most_common_event_types': list(common_event_types),
        })
