from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test users with different roles for testing authentication'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-admin',
            action='store_true',
            help='Create an admin user',
        )
        parser.add_argument(
            '--create-test-users',
            action='store_true',
            help='Create test users with different roles',
        )

    def handle(self, *args, **options):
        if options['create_admin']:
            self.create_admin_user()
        
        if options['create_test_users']:
            self.create_test_users()

    def create_admin_user(self):
        """Create an admin user for testing."""
        try:
            admin_user = User.objects.create_user(
                email='admin@wingz.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                phone_number='555-0001',
                role='admin'
            )
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created admin user: {admin_user.email}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating admin user: {e}')
            )

    def create_test_users(self):
        """Create test users with different roles."""
        test_users = [
            {
                'email': 'driver@wingz.com',
                'password': 'driver123',
                'first_name': 'John',
                'last_name': 'Driver',
                'phone_number': '555-0002',
                'role': 'driver'
            },
            {
                'email': 'rider@wingz.com',
                'password': 'rider123',
                'first_name': 'Jane',
                'last_name': 'Rider',
                'phone_number': '555-0003',
                'role': 'rider'
            },
            {
                'email': 'dispatcher@wingz.com',
                'password': 'dispatcher123',
                'first_name': 'Bob',
                'last_name': 'Dispatcher',
                'phone_number': '555-0004',
                'role': 'dispatcher'
            }
        ]

        for user_data in test_users:
            try:
                user = User.objects.create_user(**user_data)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created {user_data["role"]} user: {user.email}'
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error creating {user_data["role"]} user: {e}'
                    )
                )
