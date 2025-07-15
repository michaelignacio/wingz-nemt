from rest_framework import serializers
from .models import User, RideEvent, Ride
from django.utils import timezone


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.
    Handles serialization/deserialization of User instances for the API.
    """
    
    full_name = serializers.ReadOnlyField(help_text="User's full name (computed field)")
    is_admin = serializers.SerializerMethodField(help_text="Whether user has admin role")
    
    class Meta:
        model = User
        fields = [
            'id_user',
            'role', 
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'full_name',
            'is_admin',
            'is_active',
            'date_joined',
        ]
        read_only_fields = ['id_user', 'date_joined', 'full_name', 'is_admin']
    
    def get_is_admin(self, obj):
        """Return whether the user has admin role."""
        return obj.is_admin()
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            if not self.instance or self.instance.email != value:
                raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_role(self, value):
        """Validate role is one of the allowed choices."""
        allowed_roles = [choice[0] for choice in User.ROLE_CHOICES]
        if value not in allowed_roles:
            raise serializers.ValidationError(f"Role must be one of: {', '.join(allowed_roles)}")
        return value


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users.
    Includes password handling for user creation.
    """
    
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="User's password (minimum 8 characters)"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        help_text="Password confirmation"
    )
    
    class Meta:
        model = User
        fields = [
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'phone_number',
            'role',
        ]
    
    def validate(self, attrs):
        """Validate password confirmation matches."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs
    
    def create(self, validated_data):
        """Create a new user with encrypted password."""
        # Remove password_confirm from validated data
        validated_data.pop('password_confirm', None)
        
        # Extract password
        password = validated_data.pop('password')
        
        # Create user
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserSummarySerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for User model when used as nested field.
    Used in Ride serializers to avoid circular imports and reduce payload size.
    """
    
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id_user',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
        ]
        read_only_fields = ['id_user', 'full_name']


class RideEventSerializer(serializers.ModelSerializer):
    """
    Serializer for the RideEvent model.
    Handles serialization/deserialization of RideEvent instances.
    """
    
    # Add computed fields
    is_pickup_event = serializers.SerializerMethodField(help_text="Whether this is a pickup event")
    is_dropoff_event = serializers.SerializerMethodField(help_text="Whether this is a dropoff event")
    time_since_created = serializers.SerializerMethodField(help_text="Time elapsed since event creation")
    
    class Meta:
        model = RideEvent
        fields = [
            'id_ride_event',
            'id_ride',
            'description',
            'created_at',
            'is_pickup_event',
            'is_dropoff_event',
            'time_since_created',
        ]
        read_only_fields = ['id_ride_event', 'created_at', 'is_pickup_event', 'is_dropoff_event', 'time_since_created']
    
    def get_is_pickup_event(self, obj):
        """Return whether this is a pickup event."""
        return obj.is_pickup_event()
    
    def get_is_dropoff_event(self, obj):
        """Return whether this is a dropoff event."""
        return obj.is_dropoff_event()
    
    def get_time_since_created(self, obj):
        """Return time elapsed since event creation in human-readable format."""
        now = timezone.now()
        delta = now - obj.created_at
        
        if delta.days > 0:
            return f"{delta.days} days ago"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            return f"{hours} hours ago"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"


class RideEventCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new ride events.
    Simplified for creation purposes.
    """
    
    class Meta:
        model = RideEvent
        fields = [
            'id_ride',
            'description',
        ]
    
    def validate_description(self, value):
        """Validate description is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Description cannot be empty.")
        return value.strip()


class TodaysRideEventSerializer(serializers.ModelSerializer):
    """
    Optimized serializer for today's ride events (last 24 hours).
    Used in the Ride serializer for the todays_ride_events field.
    Minimal fields for performance as specified in requirements.
    """
    
    class Meta:
        model = RideEvent
        fields = [
            'id_ride_event',
            'description',
            'created_at',
        ]
        read_only_fields = ['id_ride_event', 'created_at']


class RideSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for the Ride model.
    Includes nested relationships and the special todays_ride_events field.
    Optimized for minimal database queries as per specification.
    """
    
    # Nested user information
    id_rider = UserSummarySerializer(read_only=True)
    id_driver = UserSummarySerializer(read_only=True)
    
    # Related ride events with performance optimization
    todays_ride_events = serializers.SerializerMethodField(
        help_text="Ride events from the last 24 hours (performance optimized)"
    )
    
    # Computed fields
    pickup_location = serializers.SerializerMethodField(help_text="Pickup coordinates as [lat, lng]")
    dropoff_location = serializers.SerializerMethodField(help_text="Dropoff coordinates as [lat, lng]")
    
    # Distance calculation field (for GPS sorting)
    distance_from_point = serializers.SerializerMethodField(
        help_text="Distance from specified point (only included when GPS sorting is used)"
    )
    
    class Meta:
        model = Ride
        fields = [
            'id_ride',
            'status',
            'id_rider',
            'id_driver',
            'pickup_latitude',
            'pickup_longitude',
            'dropoff_latitude',
            'dropoff_longitude',
            'pickup_time',
            'pickup_location',
            'dropoff_location',
            'todays_ride_events',
            'distance_from_point',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id_ride', 
            'pickup_location', 
            'dropoff_location', 
            'todays_ride_events',
            'distance_from_point',
            'created_at', 
            'updated_at'
        ]
    
    def get_todays_ride_events(self, obj):
        """
        Get ride events from the last 24 hours.
        This implements the performance optimization mentioned in the specification.
        """
        todays_events = obj.get_todays_ride_events()
        return TodaysRideEventSerializer(todays_events, many=True).data
    
    def get_pickup_location(self, obj):
        """Return pickup coordinates as [latitude, longitude]."""
        return [obj.pickup_latitude, obj.pickup_longitude]
    
    def get_dropoff_location(self, obj):
        """Return dropoff coordinates as [latitude, longitude]."""
        return [obj.dropoff_latitude, obj.dropoff_longitude]
    
    def get_distance_from_point(self, obj):
        """
        Calculate distance from a specified GPS point.
        Only included when GPS sorting is requested.
        """
        # Check if GPS coordinates were provided in context
        request = self.context.get('request')
        if request and hasattr(request, 'gps_latitude') and hasattr(request, 'gps_longitude'):
            return round(obj.distance_from_point(request.gps_latitude, request.gps_longitude), 2)
        return None


class RideCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new rides.
    Uses user IDs instead of nested objects for creation.
    """
    
    id_rider = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role__in=['rider', 'admin']),
        help_text="ID of the rider user"
    )
    id_driver = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role__in=['driver', 'admin']),
        help_text="ID of the driver user"
    )
    
    class Meta:
        model = Ride
        fields = [
            'status',
            'id_rider',
            'id_driver',
            'pickup_latitude',
            'pickup_longitude',
            'dropoff_latitude',
            'dropoff_longitude',
            'pickup_time',
        ]
    
    def validate(self, attrs):
        """Validate ride data."""
        # Ensure rider and driver are different users
        if attrs['id_rider'] == attrs['id_driver']:
            raise serializers.ValidationError("Rider and driver must be different users.")
        
        # Validate coordinates are within reasonable bounds
        for coord_name, coord_value in [
            ('pickup_latitude', attrs['pickup_latitude']),
            ('pickup_longitude', attrs['pickup_longitude']),
            ('dropoff_latitude', attrs['dropoff_latitude']),
            ('dropoff_longitude', attrs['dropoff_longitude']),
        ]:
            if coord_name.endswith('_latitude'):
                if not -90 <= coord_value <= 90:
                    raise serializers.ValidationError(f"{coord_name} must be between -90 and 90 degrees.")
            else:  # longitude
                if not -180 <= coord_value <= 180:
                    raise serializers.ValidationError(f"{coord_name} must be between -180 and 180 degrees.")
        
        return attrs


class RideListSerializer(serializers.ModelSerializer):
    """
    Optimized serializer for ride list view.
    Minimal fields for better performance when listing many rides.
    """
    
    rider_email = serializers.CharField(source='id_rider.email', read_only=True)
    driver_email = serializers.CharField(source='id_driver.email', read_only=True)
    rider_name = serializers.CharField(source='id_rider.full_name', read_only=True)
    driver_name = serializers.CharField(source='id_driver.full_name', read_only=True)
    
    # Only include today's events count for performance
    todays_events_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Ride
        fields = [
            'id_ride',
            'status',
            'rider_email',
            'driver_email',
            'rider_name',
            'driver_name',
            'pickup_time',
            'todays_events_count',
            'pickup_latitude',
            'pickup_longitude',
        ]
    
    def get_todays_events_count(self, obj):
        """Return count of today's events for performance."""
        return obj.get_todays_ride_events().count()
