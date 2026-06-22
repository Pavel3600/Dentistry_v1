"""
Создаёт/обновляет Django-пользователей (auth_user + app_userprofile).
Данные клиники хранятся в FastAPI — для их заполнения запустите:
    python scripts/seed_accounts.py  (из папки Api/)

Запуск: python manage.py seed_django_users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from app.models import UserProfile

ACCOUNTS = [
    # (username, password, role, first_name, last_name, is_superuser)
    ("admin",   "admin123",   "admin",   "Администратор", "Системы",    True),
    ("manager", "manager123", "manager", "Менеджер",      "Клиники",    False),
    ("dentist", "dentist123", "dentist", "Врач",          "Стоматолог", False),
]


class Command(BaseCommand):
    help = "Создаёт/обновляет Django auth-учётки: admin, manager, dentist."

    def handle(self, *args, **options):
        for username, password, role, first, last, is_super in ACCOUNTS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@dentaclinic.local"},
            )
            user.first_name = first
            user.last_name = last
            user.is_staff = is_super
            user.is_superuser = is_super
            user.is_active = True
            user.set_password(password)
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()

            action = "создан" if created else "обновлён"
            self.stdout.write(self.style.SUCCESS(f"  [{role}] {username} / {password} — {action}"))

        self.stdout.write(self.style.SUCCESS(
            "\nDjango-учётки готовы. Данные клиники — python scripts/seed_accounts.py (Api/)"
        ))
