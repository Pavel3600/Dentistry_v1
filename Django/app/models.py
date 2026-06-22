# app/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone


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
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"


class Clients(models.Model):
    """Клиент (учётная запись в системе FastAPI), синхронизируется с Django User."""
    login = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=20, default='patient')

    class Meta:
        db_table = 'app_clients'

    def __str__(self):
        return self.login


class Service(models.Model):
    """Медицинская услуга."""
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    cost = models.FloatField(default=0.0)
    duration_minutes = models.IntegerField(default=30)
    material_cost = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.code} — {self.name}"


class Material(models.Model):
    """Расходный материал."""
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=50)
    price_per_unit = models.FloatField(default=0.0)

    def __str__(self):
        return self.name


class MKBSCode(models.Model):
    """Код по МКБ-С (стоматологическая)."""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=500)
    category = models.CharField(max_length=50, default='diagnosis')
    parent_code = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} — {self.name}"


class MkbCode(MKBSCode):
    """Прокси-модель MKBSCode для удобного импорта."""
    class Meta:
        proxy = True


class Patient(models.Model):
    """Пациент клиники."""
    GENDER_CHOICES = [('M', 'Мужской'), ('F', 'Женский'), ('O', 'Другой')]

    full_name = models.CharField(max_length=150)
    birth_date = models.DateTimeField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=300, blank=True)
    card_number = models.CharField(max_length=50, blank=True)
    user_id = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.card_number:
            year = timezone.now().year
            super().save(*args, **kwargs)
            self.card_number = f'K-{year}-{self.pk:05d}'
            Patient.objects.filter(pk=self.pk).update(card_number=self.card_number)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name


class PatientMedicalInfo(models.Model):
    """Медицинская информация пациента (аллергии, хронические заболевания)."""
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='medical_info')
    allergies = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)
    blood_type = models.CharField(max_length=5, blank=True)
    notes = models.TextField(blank=True)

    @property
    def has_alerts(self):
        return bool(self.allergies or self.contraindications)

    def __str__(self):
        return f"MedInfo for {self.patient}"


class Appointment(models.Model):
    """Запись на приём."""
    STATUS_CHOICES = [
        ('scheduled', 'Запланирован'),
        ('completed', 'Завершён'),
        ('cancelled', 'Отменён'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    datetime = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(default=timezone.now)

    @property
    def patient_id(self):
        return self.patient_id_id if hasattr(self, 'patient_id_id') else self.patient.id

    def __str__(self):
        return f"Appointment #{self.pk} [{self.status}]"


class Visit(models.Model):
    """Визит (медицинская запись после приёма)."""
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='visit')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='visits')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='visits')
    visit_date = models.DateTimeField(default=timezone.now)
    anamnesis = models.TextField(blank=True)
    examination_results = models.TextField(blank=True)
    diagnosis = models.ForeignKey(MKBSCode, null=True, blank=True, on_delete=models.SET_NULL)
    treatment_plan = models.TextField(blank=True)
    prescription = models.TextField(blank=True)
    tooth_formula = models.CharField(max_length=200, blank=True)
    report = models.TextField(blank=True)

    def __str__(self):
        return f"Visit #{self.pk} on {self.visit_date.date()}"


class Procedure(models.Model):
    """Процедура, выполненная во время визита."""
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='procedures')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    total_cost = models.FloatField(default=0.0)

    def save(self, *args, **kwargs):
        self.total_cost = self.service.cost * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Procedure: {self.service.name} x{self.quantity}"


class MaterialUsage(models.Model):
    """Использование материала в процедуре."""
    procedure = models.ForeignKey(Procedure, on_delete=models.CASCADE, related_name='material_usages')
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity = models.FloatField(default=1.0)
    cost = models.FloatField(default=0.0)

    def save(self, *args, **kwargs):
        self.cost = self.material.price_per_unit * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.material.name} x{self.quantity}"


class Investigation(models.Model):
    """Исследование (рентген, анализ и т.п.)."""
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='investigations')
    type = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.type} (Visit #{self.visit_id})"


class VisitReport(models.Model):
    """Отчёт врача о визите."""
    visit = models.OneToOneField('Visit', on_delete=models.CASCADE, related_name='report_obj')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=255, blank=True)
    summary = models.TextField()
    recommendations = models.TextField(blank=True)
    complications = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Отчёт о визите #{self.visit_id}"


class AppointmentLog(models.Model):
    """Лог изменений статуса записи."""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='logs')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.old_status} → {self.new_status}"


class Study(models.Model):
    """Исследование пациента (рентген, анализ и т.п.)."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='studies')
    study_type = models.CharField(max_length=100)
    date = models.DateTimeField(default=timezone.now)
    result = models.TextField(blank=True)
    file_path = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return f"{self.study_type} for {self.patient}"


class Referral(models.Model):
    """Направление к специалисту."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='referrals')
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    to_specialist = models.CharField(max_length=100)
    reason = models.TextField()
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Referral → {self.to_specialist}"


class WorkOrder(models.Model):
    """Наряд-заказ (зубопротезирование)."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='work_orders')
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(default=timezone.now)
    manipulations = models.TextField()
    materials = models.TextField()
    labor_cost = models.FloatField(default=0.0)

    def __str__(self):
        return f"WorkOrder #{self.pk}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создаёт UserProfile и Clients при регистрации нового пользователя."""
    if created:
        UserProfile.objects.get_or_create(user=instance, defaults={'role': 'dentist'})
        Clients.objects.get_or_create(login=instance.username, defaults={'role': 'patient'})
