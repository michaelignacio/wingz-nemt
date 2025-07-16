from django.core.management.base import BaseCommand
from django.utils import timezone
from rides.models import User, Ride, RideEvent
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Populate the database with test users and rides.'

    def handle(self, *args, **options):
        # Create users
        users = []
        roles = ['rider', 'driver']
        for i in range(1, 7):
            for role in roles:
                email = f'{role}{i}@example.com'
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'first_name': f'{role.capitalize()}{i}',
                        'last_name': 'Test',
                        'phone_number': f'555-000{i}{1 if role=="rider" else 2}',
                        'role': role,
                        'is_active': True,
                    }
                )
                users.append(user)
        # Add at least one admin and one dispatcher
        admin, _ = User.objects.get_or_create(
            email='admin@example.com',
            defaults={
                'first_name': 'Admin',
                'last_name': 'User',
                'phone_number': '555-ADMIN',
                'role': 'admin',
                'is_active': True,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        dispatcher, _ = User.objects.get_or_create(
            email='dispatcher@example.com',
            defaults={
                'first_name': 'Dispatcher',
                'last_name': 'User',
                'phone_number': '555-DISPATCH',
                'role': 'dispatcher',
                'is_active': True,
            }
        )
        users.extend([admin, dispatcher])
        riders = [u for u in users if u.role == 'rider']
        drivers = [u for u in users if u.role == 'driver']

        # Create rides
        ride_count = Ride.objects.count()
        rides_to_create = max(0, 12 - ride_count)
        for i in range(rides_to_create):
            rider = random.choice(riders)
            driver = random.choice(drivers)
            pickup_lat = 37.77 + random.uniform(-0.01, 0.01)
            pickup_lon = -122.41 + random.uniform(-0.01, 0.01)
            dropoff_lat = 37.78 + random.uniform(-0.01, 0.01)
            dropoff_lon = -122.42 + random.uniform(-0.01, 0.01)
            pickup_time = timezone.now() - timedelta(hours=random.randint(0, 48))
            status = random.choice(['en-route', 'pickup', 'dropoff', 'completed', 'cancelled'])
            ride = Ride.objects.create(
                status=status,
                id_rider=rider,
                id_driver=driver,
                pickup_latitude=pickup_lat,
                pickup_longitude=pickup_lon,
                dropoff_latitude=dropoff_lat,
                dropoff_longitude=dropoff_lon,
                pickup_time=pickup_time
            )
            # Create RideEvents for each ride
            # Always create at least one event in the last 24 hours
            event_time = timezone.now() - timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
            RideEvent.objects.create(
                id_ride=ride,
                description=f"Status changed to {status}",
                created_at=event_time
            )
            # Optionally add a pickup and dropoff event, possibly outside 24h
            if random.random() > 0.5:
                RideEvent.objects.create(
                    id_ride=ride,
                    description="Pickup completed",
                    created_at=pickup_time + timedelta(minutes=5)
                )
            if random.random() > 0.5:
                RideEvent.objects.create(
                    id_ride=ride,
                    description="Dropoff completed",
                    created_at=pickup_time + timedelta(minutes=30)
                )
        self.stdout.write(self.style.SUCCESS('Test users and rides created.'))
