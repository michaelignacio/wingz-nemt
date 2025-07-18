from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta


class CustomUserManager(BaseUserManager):
    """Custom user manager for the User model."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with an email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model based on the specification.
    Uses email as the unique identifier instead of username.
    """
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('driver', 'Driver'),
        ('rider', 'Rider'),
        ('dispatcher', 'Dispatcher'),
    ]
    
    id_user = models.AutoField(primary_key=True, help_text="Primary key")
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES,
        default='rider',
        help_text="User role (admin, driver, rider, dispatcher)"
    )
    first_name = models.CharField(max_length=150, help_text="User's first name")
    last_name = models.CharField(max_length=150, help_text="User's last name")
    email = models.EmailField(unique=True, help_text="User's email address")
    phone_number = models.CharField(max_length=20, help_text="User's phone number")
    
    # Required for Django's authentication system
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']
    
    class Meta:
        db_table = 'user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == 'admin'


class Ride(models.Model):
    """
    Ride model based on the specification.
    Represents a ride with pickup/dropoff locations and associated users.
    """
    
    STATUS_CHOICES = [
        ('en-route', 'En Route'),
        ('pickup', 'Pickup'),
        ('dropoff', 'Dropoff'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id_ride = models.AutoField(primary_key=True, help_text="Primary key")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='en-route',
        help_text="Ride status (e.g., 'en-route', 'pickup', 'dropoff')"
    )
    id_rider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='rides_as_rider',
        help_text="Foreign key referencing User(id_user) - the rider"
    )
    id_driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='rides_as_driver',
        help_text="Foreign key referencing User(id_user) - the driver"
    )
    pickup_latitude = models.FloatField(help_text="Latitude of pickup location")
    pickup_longitude = models.FloatField(help_text="Longitude of pickup location")
    dropoff_latitude = models.FloatField(help_text="Latitude of dropoff location")
    dropoff_longitude = models.FloatField(help_text="Longitude of dropoff location")
    pickup_time = models.DateTimeField(help_text="Pickup time")
    
    # Additional fields for better functionality
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ride'
        verbose_name = 'Ride'
        verbose_name_plural = 'Rides'
        ordering = ['-pickup_time']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['pickup_time']),
            models.Index(fields=['id_rider']),
            models.Index(fields=['id_driver']),
            models.Index(fields=['pickup_latitude', 'pickup_longitude']),
        ]
    
    def __str__(self):
        return f"Ride {self.id_ride} - {self.status} ({self.id_rider.email} -> {self.id_driver.email})"
    
    @property
    def pickup_location(self):
        """Return pickup coordinates as a tuple."""
        return (self.pickup_latitude, self.pickup_longitude)
    
    @property
    def dropoff_location(self):
        """Return dropoff coordinates as a tuple."""
        return (self.dropoff_latitude, self.dropoff_longitude)
    
    def distance_from_point(self, latitude, longitude):
        """
        Calculate distance from a given point to the pickup location.
        Uses Haversine formula for GPS distance calculation.
        Returns distance in kilometers.
        """
        import math
        
        # Convert latitude and longitude from degrees to radians
        lat1, lon1 = math.radians(latitude), math.radians(longitude)
        lat2, lon2 = math.radians(self.pickup_latitude), math.radians(self.pickup_longitude)
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r

    def get_todays_ride_events(self):
        """
        Get ride events from the last 24 hours for this ride.
        This is the optimized field mentioned in the specification.
        """
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        return self.ride_events.filter(created_at__gte=twenty_four_hours_ago)


class RideEventManager(models.Manager):
    """Custom manager for RideEvent with optimized queries."""
    
    def todays_events(self):
        """Return events from the last 24 hours for performance optimization."""
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        return self.filter(created_at__gte=twenty_four_hours_ago)
    
    def for_ride(self, ride_id):
        """Get all events for a specific ride."""
        return self.filter(id_ride_id=ride_id)


class RideEvent(models.Model):
    """
    RideEvent model based on the specification.
    Represents events that occur during a ride (pickup, dropoff, etc.).
    """
    
    id_ride_event = models.AutoField(primary_key=True, help_text="Primary key")
    id_ride = models.ForeignKey(
        Ride,
        on_delete=models.CASCADE,
        related_name='ride_events',
        help_text="Foreign key referencing Ride(id_ride)"
    )
    description = models.CharField(
        max_length=255,
        help_text="Description of the ride event"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp of when the event occurred"
    )
    
    objects = RideEventManager()
    
    class Meta:
        db_table = 'ride_event'
        verbose_name = 'Ride Event'
        verbose_name_plural = 'Ride Events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['id_ride']),
            models.Index(fields=['created_at']),
            models.Index(fields=['id_ride', 'created_at']),  # Compound index for performance
        ]
    
    def __str__(self):
        return f"Event {self.id_ride_event}: {self.description} (Ride {self.id_ride_id})"
    
    @classmethod
    def create_status_change_event(cls, ride, new_status):
        """
        Create a standardized status change event.
        This follows the specification format for pickup/dropoff events.
        """
        description = f"Status changed to {new_status}"
        return cls.objects.create(id_ride=ride, description=description)
    
    def is_pickup_event(self):
        """Check if this is a pickup event."""
        return 'pickup' in self.description.lower()
    
    def is_dropoff_event(self):
        """Check if this is a dropoff event."""
        return 'dropoff' in self.description.lower()
