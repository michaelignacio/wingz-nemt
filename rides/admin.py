from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Ride, RideEvent


class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model."""
    
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('email',)
    filter_horizontal = ()
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')


class RideEventInline(admin.TabularInline):
    """Inline admin for RideEvent within Ride admin."""
    model = RideEvent
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('description', 'created_at')


class RideEventAdmin(admin.ModelAdmin):
    """Admin configuration for the RideEvent model."""
    
    list_display = ('id_ride_event', 'id_ride', 'description', 'created_at')
    list_filter = ('created_at', 'id_ride__status')
    search_fields = ('description', 'id_ride__id_ride')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Event Information', {
            'fields': ('id_ride', 'description')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance."""
        return super().get_queryset(request).select_related('id_ride')


class RideAdmin(admin.ModelAdmin):
    """Admin configuration for the Ride model."""
    
    list_display = ('id_ride', 'status', 'id_rider', 'id_driver', 'pickup_time', 'created_at')
    list_filter = ('status', 'pickup_time', 'created_at')
    search_fields = ('id_rider__email', 'id_driver__email', 'id_rider__first_name', 'id_rider__last_name')
    ordering = ('-pickup_time',)
    date_hierarchy = 'pickup_time'
    inlines = [RideEventInline]
    
    fieldsets = (
        ('Ride Information', {
            'fields': ('status', 'pickup_time')
        }),
        ('Users', {
            'fields': ('id_rider', 'id_driver')
        }),
        ('Pickup Location', {
            'fields': ('pickup_latitude', 'pickup_longitude')
        }),
        ('Dropoff Location', {
            'fields': ('dropoff_latitude', 'dropoff_longitude')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    inlines = [RideEventInline]
    
    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance."""
        return super().get_queryset(request).select_related('id_rider', 'id_driver')


admin.site.register(User, UserAdmin)
admin.site.register(Ride, RideAdmin)
admin.site.register(RideEvent, RideEventAdmin)
