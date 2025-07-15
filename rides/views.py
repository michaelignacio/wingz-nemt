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
    ordering_fields = ['id_user', 'first_name', 'last_name', 'email', 'date_joined']
    ordering = ['-date_joined']  # Default ordering
    
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
        ).order_by('-pickup_time')
        
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
    filterset_fields = ['description', 'id_ride', 'id_ride__status']
    search_fields = ['description', 'id_ride__id_rider__email', 'id_ride__id_driver__email']
    ordering_fields = ['id_ride_event', 'created_at', 'description']
    ordering = ['-created_at']  # Default ordering by most recent events
    
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
        description = self.request.query_params.get('description', None)
        if description:
            queryset = queryset.filter(description__icontains=description)
        
        # Filter by date range if specified
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            try:
                from datetime import datetime
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                queryset = queryset.filter(created_at__gte=start_datetime)
            except ValueError:
                pass  # Invalid date format, ignore filter
        
        if end_date:
            try:
                from datetime import datetime
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                queryset = queryset.filter(created_at__lte=end_datetime)
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
            created_at__gte=twenty_four_hours_ago
        ).order_by('-created_at')
        
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
        
        events = self.get_queryset().filter(id_ride=ride).order_by('created_at')
        serializer = RideEventSerializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def event_types(self, request):
        """
        Get all unique event types (descriptions) in the system.
        """
        event_types = RideEvent.objects.values_list(
            'description', flat=True
        ).distinct().order_by('description')
        
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
        todays_events = RideEvent.objects.filter(created_at__gte=twenty_four_hours_ago).count()
        
        # Events from last 7 days
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        weekly_events = RideEvent.objects.filter(created_at__gte=seven_days_ago).count()
        
        # Most common event types
        from django.db.models import Count
        common_event_types = RideEvent.objects.values('description').annotate(
            count=Count('description')
        ).order_by('-count')[:5]
        
        return Response({
            'total_events': total_events,
            'todays_events': todays_events,
            'weekly_events': weekly_events,
            'most_common_event_types': list(common_event_types),
        })


class RideViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Ride model with complex operations.
    Includes GPS sorting, performance optimizations, and the special todays_ride_events field.
    Only accessible by admin users as per specification.
    """
    
    queryset = Ride.objects.select_related('id_rider', 'id_driver').prefetch_related('ride_events').all()
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtering options
    filterset_fields = ['status', 'id_rider', 'id_driver']
    search_fields = [
        'id_rider__first_name', 'id_rider__last_name', 'id_rider__email',
        'id_driver__first_name', 'id_driver__last_name', 'id_driver__email'
    ]
    ordering_fields = ['id_ride', 'pickup_time', 'status']
    ordering = ['-pickup_time']  # Default ordering
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return RideCreateSerializer
        elif self.action == 'list':
            return RideListSerializer
        return RideSerializer
    
    def get_serializer_context(self):
        """
        Add GPS coordinates to serializer context for distance calculations.
        """
        context = super().get_serializer_context()
        
        # Add GPS coordinates from request parameters for distance calculations
        gps_lat = self.request.query_params.get('gps_latitude')
        gps_lng = self.request.query_params.get('gps_longitude')
        
        if gps_lat and gps_lng:
            try:
                context['request'].gps_latitude = float(gps_lat)
                context['request'].gps_longitude = float(gps_lng)
            except (ValueError, TypeError):
                pass  # Invalid GPS coordinates, ignore
        
        return context
    
    def get_queryset(self):
        """
        Optimized queryset with GPS sorting and filtering options.
        """
        queryset = Ride.objects.select_related(
            'id_rider', 
            'id_driver'
        ).prefetch_related('ride_events').all()
        
        # Filter by status if specified
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by rider if specified
        rider_id = self.request.query_params.get('rider_id', None)
        if rider_id:
            queryset = queryset.filter(id_rider=rider_id)
        
        # Filter by driver if specified
        driver_id = self.request.query_params.get('driver_id', None)
        if driver_id:
            queryset = queryset.filter(id_driver=driver_id)
        
        # Filter by date range if specified
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            try:
                from datetime import datetime
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                queryset = queryset.filter(pickup_time__gte=start_datetime)
            except ValueError:
                pass
        
        if end_date:
            try:
                from datetime import datetime
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                queryset = queryset.filter(pickup_time__lte=end_datetime)
            except ValueError:
                pass
        
        # GPS sorting if coordinates provided
        gps_lat = self.request.query_params.get('gps_latitude')
        gps_lng = self.request.query_params.get('gps_longitude')
        
        if gps_lat and gps_lng:
            try:
                lat = float(gps_lat)
                lng = float(gps_lng)
                
                # Add distance annotation for sorting
                from django.db.models import Case, When, FloatField
                from django.db.models.functions import Sqrt, Power
                
                # Calculate distance using Haversine approximation
                queryset = queryset.extra(
                    select={
                        'distance': '''
                            6371 * acos(
                                cos(radians(%s)) * cos(radians(pickup_latitude)) *
                                cos(radians(pickup_longitude) - radians(%s)) +
                                sin(radians(%s)) * sin(radians(pickup_latitude))
                            )
                        '''
                    },
                    select_params=[lat, lng, lat]
                ).order_by('distance')
                
            except (ValueError, TypeError):
                pass  # Invalid GPS coordinates, ignore sorting
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """
        Create a new ride with proper validation.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ride = serializer.save()
        
        # Return full ride data using RideSerializer
        response_serializer = RideSerializer(ride, context=self.get_serializer_context())
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """
        Update ride with partial update support.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        ride = serializer.save()
        
        return Response(RideSerializer(ride, context=self.get_serializer_context()).data)
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        Get rides near a specific GPS location.
        Requires gps_latitude, gps_longitude, and radius (in km) parameters.
        """
        gps_lat = request.query_params.get('gps_latitude')
        gps_lng = request.query_params.get('gps_longitude')
        radius = request.query_params.get('radius', 10)  # Default 10km radius
        
        if not gps_lat or not gps_lng:
            return Response(
                {'error': 'gps_latitude and gps_longitude parameters are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lat = float(gps_lat)
            lng = float(gps_lng)
            radius_km = float(radius)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid GPS coordinates or radius'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find rides within radius using Haversine formula
        nearby_rides = self.get_queryset().extra(
            select={
                'distance': '''
                    6371 * acos(
                        cos(radians(%s)) * cos(radians(pickup_latitude)) *
                        cos(radians(pickup_longitude) - radians(%s)) +
                        sin(radians(%s)) * sin(radians(pickup_latitude))
                    )
                '''
            },
            select_params=[lat, lng, lat],
            where=['6371 * acos(cos(radians(%s)) * cos(radians(pickup_latitude)) * cos(radians(pickup_longitude) - radians(%s)) + sin(radians(%s)) * sin(radians(pickup_latitude))) <= %s'],
            params=[lat, lng, lat, radius_km]
        ).order_by('distance')
        
        serializer = RideListSerializer(nearby_rides, many=True, context=self.get_serializer_context())
        return Response({
            'rides': serializer.data,
            'center_point': {'latitude': lat, 'longitude': lng},
            'radius_km': radius_km,
            'count': nearby_rides.count()
        })
    
    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        """
        Get all events for a specific ride with today's events highlighted.
        """
        ride = self.get_object()
        
        # Get all events
        all_events = ride.ride_events.all().order_by('created_at')
        
        # Get today's events
        todays_events = ride.get_todays_ride_events()
        
        return Response({
            'ride_id': ride.id_ride,
            'all_events': RideEventSerializer(all_events, many=True).data,
            'todays_events': TodaysRideEventSerializer(todays_events, many=True).data,
            'todays_events_count': todays_events.count(),
            'total_events_count': all_events.count(),
        })
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get all active rides (not completed or cancelled).
        """
        active_rides = self.get_queryset().exclude(status__in=['completed', 'cancelled'])
        serializer = RideListSerializer(active_rides, many=True, context=self.get_serializer_context())
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get ride statistics with breakdown by status.
        """
        from django.db.models import Count
        from datetime import datetime, timezone, timedelta
        
        # Overall stats
        total_rides = Ride.objects.count()
        
        # Status breakdown
        status_stats = Ride.objects.values('status').annotate(
            count=Count('status')
        ).order_by('status')
        
        # Recent rides (last 7 days)
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_rides = Ride.objects.filter(pickup_time__gte=seven_days_ago).count()
        
        # Today's rides
        today = datetime.now(timezone.utc).date()
        todays_rides = Ride.objects.filter(pickup_time__date=today).count()
        
        return Response({
            'total_rides': total_rides,
            'todays_rides': todays_rides,
            'recent_rides': recent_rides,
            'status_breakdown': list(status_stats),
        })
