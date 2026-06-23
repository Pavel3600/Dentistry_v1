from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile


# ==================== ФОРМЫ АВТОРИЗАЦИИ И РЕГИСТРАЦИИ ====================

class RegistrationForm(UserCreationForm):
    """Форма публичной регистрации. Роль всегда 'patient'."""
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        role = 'patient'

        if commit:
            user.save()
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()

            try:
                from app.services.fastapi_client import sync_user_to_fastapi
                sync_user_to_fastapi(user, role)
            except Exception:
                pass

        return user


# ==================== ФОРМЫ ПАЦИЕНТОВ ====================

class PatientForm(forms.Form):
    """Форма создания и редактирования пациента (данные уходят в FastAPI)."""
    GENDER_CHOICES = [('M', 'Мужской'), ('F', 'Женский'), ('O', 'Другой')]

    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванов Иван Иванович'})
    )
    birth_date = forms.DateTimeField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 000-00-00'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    user_id = forms.IntegerField(required=False, widget=forms.HiddenInput())


class PatientMedicalInfoForm(forms.Form):
    """Аллергии и мед. предупреждения о пациенте (данные в FastAPI)."""
    allergies = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
    chronic_conditions = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
    contraindications = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
    blood_type = forms.ChoiceField(
        required=False,
        choices=[('', '—'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
                 ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))


# ==================== ФОРМЫ ВРАЧЕЙ ====================

class DoctorForm(forms.Form):
    """Создание врача-стоматолога (User + UserProfile)."""
    username = forms.CharField(
        label='Логин', max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'i.petrov'}),
    )
    first_name = forms.CharField(label='Имя', max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Фамилия', max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email', required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Пароль', min_length=4, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    specialization = forms.CharField(label='Специализация', max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(label='Телефон', max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    cabinet = forms.CharField(label='Кабинет', max_length=10, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Пользователь с таким логином уже существует.')
        return username

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            email=data.get('email', ''),
            first_name=data['first_name'],
            last_name=data['last_name'],
        )
        profile = user.profile
        profile.role = 'dentist'
        profile.specialization = data.get('specialization', '')
        profile.phone = data.get('phone', '')
        profile.cabinet = data.get('cabinet', '')
        profile.save()
        # Создаём или обновляем локальную запись Clients
        from .models import Clients
        Clients.objects.update_or_create(
            login=user.username,
            defaults={'role': 'dentist'},
        )
        # Синхронизируем с FastAPI (необязательно)
        try:
            from .controllers import ClientController
            ClientController.create({'login': user.username, 'password': data['password'], 'role': 'dentist'})
        except Exception:
            pass
        return user


class ManagerForm(forms.Form):
    """Создание менеджера регистратуры (User + UserProfile)."""
    username = forms.CharField(
        label='Логин', max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'manager.ivanova'}),
    )
    first_name = forms.CharField(label='Имя', max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Фамилия', max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email', required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Пароль', min_length=4, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(label='Телефон', max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Пользователь с таким логином уже существует.')
        return username

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            email=data.get('email', ''),
            first_name=data['first_name'],
            last_name=data['last_name'],
        )
        profile = user.profile
        profile.role = 'manager'
        profile.phone = data.get('phone', '')
        profile.save()
        from .models import Clients
        Clients.objects.update_or_create(
            login=user.username,
            defaults={'role': 'manager'},
        )
        return user


# ==================== ФОРМЫ ОТЧЁТОВ ====================

class VisitReportForm(forms.Form):
    """Отчёт о приёме (данные уходят в FastAPI)."""
    title = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    summary = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}))
    recommendations = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    complications = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))


# ==================== ФОРМЫ ЗАПИСЕЙ НА ПРИЕМ ====================

class AppointmentForm(forms.Form):
    """Форма создания записи на приём."""
    patient_id = forms.IntegerField(
        label='ID Пациента',
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    doctor_id = forms.IntegerField(
        label='ID Врача',
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    datetime = forms.DateTimeField(
        label='Дата и время',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    def save(self):
        from .models import Appointment, Patient
        from django.contrib.auth.models import User as _User
        data = self.cleaned_data
        patient = Patient.objects.get(pk=data['patient_id'])
        doctor = _User.objects.get(pk=data['doctor_id'])
        return Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            datetime=data['datetime'],
            status='scheduled',
        )


class AdminAppointmentForm(forms.Form):
    """Расширенная форма записи для Администратора."""
    patient_id = forms.IntegerField(label='ID Пациента', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    doctor_id = forms.IntegerField(label='ID Врача', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    datetime = forms.DateTimeField(
        label='Дата и время',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    status = forms.ChoiceField(
        choices=[('scheduled', 'Запланирован'), ('completed', 'Завершён'), ('cancelled', 'Отменён')],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


# ==================== ФОРМЫ МЕДИЦИНСКИХ ДАННЫХ ====================

class VisitForm(forms.Form):
    """Форма визита (данные уходят в FastAPI)."""
    anamnesis = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    examination_results = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    diagnosis_id = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    treatment_plan = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    tooth_formula = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))


class ProcedureForm(forms.Form):
    """Форма процедуры."""
    from .models import Service as _Service
    service = forms.ModelChoiceField(
        queryset=_Service.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    quantity = forms.IntegerField(initial=1, min_value=1, widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}))


class ReferralForm(forms.Form):
    """Форма направления к специалисту (данные уходят в FastAPI)."""
    to_specialist = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    reason = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))


# ==================== ФОРМЫ СПРАВОЧНИКОВ (АДМИН) ====================

class ServiceForm(forms.Form):
    """Форма услуги (данные уходят в FastAPI)."""
    code = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    cost = forms.FloatField(widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    duration_minutes = forms.IntegerField(initial=30, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    material_cost = forms.FloatField(initial=0.0, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))


class MaterialForm(forms.Form):
    """Форма материала (данные уходят в FastAPI)."""
    name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    unit = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    price_per_unit = forms.FloatField(widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))


class MkbCodeForm(forms.Form):
    """Форма кода МКБ (данные уходят в FastAPI)."""
    code = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    name = forms.CharField(max_length=500, widget=forms.TextInput(attrs={'class': 'form-control'}))
    category = forms.ChoiceField(
        choices=[('diagnosis', 'Диагноз'), ('service', 'Услуга')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    parent_code = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    is_active = forms.BooleanField(required=False, initial=True)


# ==================== ФОРМЫ ПОИСКА ====================

class VisitSearchForm(forms.Form):
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False, label="Дата с"
    )
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False, label="Дата по"
    )
    patient_name = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ФИО пациента'}),
        label="ФИО Пациента"
    )
