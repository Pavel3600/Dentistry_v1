from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import UserProfile
from app.services.fastapi_client import sync_user_to_fastapi


class Command(BaseCommand):
    help = 'Синхронизация БД Django с FastAPI'

    def handle(self, *args, **options):
        self.stdout.write('Синхронизация пользователей...')

        users = User.objects.all()
        synced = 0

        for user in users:
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'patient'}
            )

            # Синхронизируем с FastAPI
            if sync_user_to_fastapi(user, profile.role):
                synced += 1
                self.stdout.write(f'  Синхронизирован: {user.username} ({profile.role})')

        self.stdout.write(self.style.SUCCESS(f'Синхронизировано {synced} пользователей'))