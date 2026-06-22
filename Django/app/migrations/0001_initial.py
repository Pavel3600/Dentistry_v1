from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """Single clean migration — only UserProfile remains in Django."""

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(
                    choices=[
                        ('dentist', 'Стоматолог'),
                        ('manager', 'Менеджер'),
                        ('admin', 'Администратор'),
                        ('patient', 'Пациент'),
                    ],
                    default='dentist',
                    max_length=20,
                )),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('specialization', models.CharField(blank=True, max_length=100)),
                ('cabinet', models.CharField(blank=True, max_length=10)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='profile',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
    ]
