from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

# Добавьте строковую ссылку на Clients вместо прямого импорта
# Это решит проблему циклической зависимости

class MKBSCode(Base):
    __tablename__ = "mkbs_codes"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(500), nullable=False)
    category = Column(String(50), nullable=False)
    parent_code = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)


class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    card_number = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("clients.id"), nullable=False, unique=True)
    full_name = Column(String, nullable=False)
    birth_date = Column(DateTime, nullable=False)
    gender = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=True)
    email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # Используем строковые имена для relationship
    user = relationship("Clients", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")
    medical_records = relationship("MedicalRecord", back_populates="patient")
    studies = relationship("Study", back_populates="patient")
    referrals = relationship("Referral", back_populates="patient")
    work_orders = relationship("WorkOrder", back_populates="patient")


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    datetime = Column(DateTime, nullable=False)
    status = Column(String, default="scheduled")
    from sqlalchemy import func
    created_at = Column(DateTime, server_default=func.now())

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Clients")


class MedicalRecord(Base):
    __tablename__ = "medical_records"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    visit_date = Column(DateTime, default=datetime.utcnow)
    complaints = Column(Text, nullable=True)
    anamnesis = Column(Text, nullable=True)
    examination = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=True)
    prescriptions = Column(Text, nullable=True)
    tooth_formula = Column(Text, nullable=True)
    alert_info = Column(Text, nullable=True)
    mkbs_code_id = Column(Integer, ForeignKey("mkbs_codes.id"), nullable=True)

    patient = relationship("Patient", back_populates="medical_records")
    doctor = relationship("Clients")
    mkbs_code = relationship("MKBSCode", foreign_keys=[mkbs_code_id])


class Study(Base):
    __tablename__ = "studies"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    study_type = Column(String, nullable=False)
    result = Column(Text, nullable=True)
    file_path = Column(String, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="studies")


class Referral(Base):
    __tablename__ = "referrals"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    to_specialist = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="referrals")
    doctor = relationship("Clients")


class WorkOrder(Base):
    __tablename__ = "work_orders"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    manipulations = Column(Text, nullable=False)
    materials = Column(Text, nullable=False)
    labor_cost = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="work_orders")
    doctor = relationship("Clients")


class Service(Base):
    """Стоматологические услуги."""
    __tablename__ = "services"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    cost = Column(Float, nullable=False)
    duration_minutes = Column(Integer, default=30)
    material_cost = Column(Float, default=0.0)

    procedures = relationship("Procedure", back_populates="service")


class Material(Base):
    """Расходные материалы."""
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    unit = Column(String(20), default="шт")
    price_per_unit = Column(Float, nullable=False)

    usages = relationship("MaterialUsage", back_populates="material")


class Visit(Base):
    """Визит/приём — связан с записью (appointment_id из FastAPI)."""
    __tablename__ = "visits"
    id = Column(Integer, primary_key=True)
    appointment_id = Column(Integer, unique=True, nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    visit_date = Column(DateTime, default=datetime.utcnow)
    anamnesis = Column(Text, default="")
    examination_results = Column(Text, default="")
    diagnosis_id = Column(Integer, ForeignKey("mkbs_codes.id"), nullable=True)
    treatment_plan = Column(Text, default="")
    prescription = Column(Text, default="")
    tooth_formula = Column(Text, default="")

    patient = relationship("Patient")
    doctor = relationship("Clients")
    diagnosis = relationship("MKBSCode")
    procedures = relationship("Procedure", back_populates="visit", cascade="all, delete-orphan")
    investigations = relationship("Investigation", back_populates="visit", cascade="all, delete-orphan")
    extracts = relationship("MedicalRecordExtract", back_populates="visit", cascade="all, delete-orphan")
    reports = relationship("VisitReport", back_populates="visit", cascade="all, delete-orphan")


class Procedure(Base):
    """Процедуры, выполненные во время визита."""
    __tablename__ = "procedures"
    id = Column(Integer, primary_key=True)
    visit_id = Column(Integer, ForeignKey("visits.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    quantity = Column(Integer, default=1)
    total_cost = Column(Float, nullable=False)

    visit = relationship("Visit", back_populates="procedures")
    service = relationship("Service", back_populates="procedures")
    material_usages = relationship("MaterialUsage", back_populates="procedure", cascade="all, delete-orphan")


class MaterialUsage(Base):
    """Использование расходных материалов в процедуре."""
    __tablename__ = "material_usages"
    id = Column(Integer, primary_key=True)
    procedure_id = Column(Integer, ForeignKey("procedures.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)

    procedure = relationship("Procedure", back_populates="material_usages")
    material = relationship("Material", back_populates="usages")


class AppointmentLog(Base):
    """Лог изменений статуса записи на приём."""
    __tablename__ = "appointment_logs"
    id = Column(Integer, primary_key=True)
    appointment_id = Column(Integer, nullable=False)
    changed_by_login = Column(String(255), nullable=True)
    old_status = Column(String(20), nullable=False)
    new_status = Column(String(20), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)
    comment = Column(Text, default="")


class Investigation(Base):
    """Исследования, проведённые во время визита."""
    __tablename__ = "investigations"
    id = Column(Integer, primary_key=True)
    visit_id = Column(Integer, ForeignKey("visits.id"), nullable=False)
    type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    result = Column(Text, default="")

    visit = relationship("Visit", back_populates="investigations")


class PatientMedicalInfo(Base):
    """Мед. предупреждения о пациенте (аллергии, хронические болезни)."""
    __tablename__ = "patient_medical_infos"
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), unique=True, nullable=False)
    allergies = Column(Text, default="")
    chronic_conditions = Column(Text, default="")
    contraindications = Column(Text, default="")
    blood_type = Column(String(4), default="")
    notes = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("Patient")


class MedicalRecordExtract(Base):
    """Выписки из медицинской карты."""
    __tablename__ = "medical_record_extracts"
    id = Column(Integer, primary_key=True)
    visit_id = Column(Integer, ForeignKey("visits.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String(300), nullable=True)

    visit = relationship("Visit", back_populates="extracts")


class VisitReport(Base):
    """Отчёт врача после приёма."""
    __tablename__ = "visit_reports"
    id = Column(Integer, primary_key=True)
    visit_id = Column(Integer, ForeignKey("visits.id"), nullable=False)
    author_login = Column(String(255), nullable=True)
    title = Column(String(200), default="Отчёт о приёме")
    summary = Column(Text, nullable=False)
    recommendations = Column(Text, default="")
    complications = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    visit = relationship("Visit", back_populates="reports")