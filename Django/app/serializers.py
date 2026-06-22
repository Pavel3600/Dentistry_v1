from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'full_name', 'email', 'role', 'phone', 'specialization', 'cabinet']

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


# --- Сериализаторы для данных из FastAPI (plain dict -> validated) ---

class PatientSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField(max_length=150)
    birth_date = serializers.DateTimeField()
    gender = serializers.ChoiceField(choices=['M', 'F', 'O'])
    phone = serializers.CharField(max_length=20)
    address = serializers.CharField(allow_blank=True, required=False)
    card_number = serializers.CharField(read_only=True)
    user_id = serializers.IntegerField(required=False, allow_null=True)


class AppointmentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    patient_id = serializers.IntegerField()
    doctor_id = serializers.IntegerField()
    datetime = serializers.DateTimeField()
    status = serializers.ChoiceField(choices=['scheduled', 'completed', 'cancelled'])
    created_at = serializers.DateTimeField(read_only=True)


class MedicalRecordSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    patient_id = serializers.IntegerField()
    doctor_id = serializers.IntegerField(read_only=True)
    visit_date = serializers.DateTimeField(read_only=True)
    complaints = serializers.CharField(allow_blank=True, required=False)
    anamnesis = serializers.CharField(allow_blank=True, required=False)
    examination = serializers.CharField(allow_blank=True, required=False)
    diagnosis = serializers.CharField(allow_blank=True, required=False)
    prescriptions = serializers.CharField(allow_blank=True, required=False)
    tooth_formula = serializers.CharField(allow_blank=True, required=False)
    mkbs_code_id = serializers.IntegerField(allow_null=True, required=False)


class MKBSCodeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    code = serializers.CharField()
    name = serializers.CharField()
    category = serializers.CharField()
    parent_code = serializers.CharField(allow_null=True, required=False)
    is_active = serializers.BooleanField()


class ServiceSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    code = serializers.CharField()
    name = serializers.CharField()
    cost = serializers.FloatField()
    duration_minutes = serializers.IntegerField()
    material_cost = serializers.FloatField()


class MaterialSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    unit = serializers.CharField()
    price_per_unit = serializers.FloatField()


class VisitSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    appointment_id = serializers.IntegerField()
    patient_id = serializers.IntegerField()
    doctor_id = serializers.IntegerField()
    visit_date = serializers.DateTimeField(read_only=True)
    anamnesis = serializers.CharField(allow_blank=True, required=False)
    examination_results = serializers.CharField(allow_blank=True, required=False)
    diagnosis_id = serializers.IntegerField(allow_null=True, required=False)
    treatment_plan = serializers.CharField(allow_blank=True, required=False)
    prescription = serializers.CharField(allow_blank=True, required=False)
    tooth_formula = serializers.CharField(allow_blank=True, required=False)


class ReferralSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    patient_id = serializers.IntegerField()
    doctor_id = serializers.IntegerField(read_only=True)
    to_specialist = serializers.CharField()
    reason = serializers.CharField()
    date = serializers.DateTimeField(read_only=True)


class WorkOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    patient_id = serializers.IntegerField()
    doctor_id = serializers.IntegerField(read_only=True)
    date = serializers.DateTimeField(read_only=True)
    manipulations = serializers.CharField()
    materials = serializers.CharField()
    labor_cost = serializers.FloatField()


class StudySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    patient_id = serializers.IntegerField()
    study_type = serializers.CharField()
    date = serializers.DateTimeField(read_only=True)
    result = serializers.CharField(allow_blank=True, required=False)
    file_path = serializers.CharField(allow_blank=True, required=False)


class StatisticsSerializer(serializers.Serializer):
    total_patients = serializers.IntegerField()
    total_appointments = serializers.IntegerField()
    completed_appointments = serializers.IntegerField()
    cancelled_appointments = serializers.IntegerField()
    scheduled_appointments = serializers.IntegerField()
    total_visits = serializers.IntegerField()
    total_revenue = serializers.FloatField()
    period_days = serializers.IntegerField()
