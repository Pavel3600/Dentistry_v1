# app/models.py
# Все бизнес-модели (пациенты, записи, визиты, услуги, материалы и пр.)
# хранятся в FastAPI и доступны через контроллеры в app/controllers/.
# Django управляет только данными аутентификации.

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


class UserProfile(models.Model):
    """Профиль Django-пользователя с ролью для разграничения доступа."""
    ROLE_CHOICES = (
        ('dentist', 'Стоматолог'),
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
        ('patient', 'Пациент'),
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='dentist')
    phone = models.CharField(max_length=20, blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    cabinet = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создаёт UserProfile при регистрации нового пользователя."""
    if created:
        UserProfile.objects.get_or_create(user=instance, defaults={'role': 'dentist'})
