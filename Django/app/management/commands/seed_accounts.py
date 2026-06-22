from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create default admin, manager, dentist accounts'

    def handle(self, *args, **options):
        accounts = [
            {'username': 'admin', 'password': 'admin123', 'role': 'admin', 'is_superuser': True},
            {'username': 'manager', 'password': 'manager123', 'role': 'manager', 'is_superuser': False},
            {'username': 'dentist', 'password': 'dentist123', 'role': 'dentist', 'is_superuser': False},
        ]
        for acc in accounts:
            user, created = User.objects.get_or_create(username=acc['username'])
            user.set_password(acc['password'])
            user.is_superuser = acc['is_superuser']
            user.is_staff = acc['is_superuser']
            user.save()
            profile = user.profile
            profile.role = acc['role']
            profile.save()
            if created:
                self.stdout.write(f"Created: {acc['username']}")
            else:
                self.stdout.write(f"Updated: {acc['username']}")
