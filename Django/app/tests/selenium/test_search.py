import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from app.models import Patient, Appointment, Visit

@pytest.mark.selenium
@pytest.mark.usefixtures("chrome_driver")
class TestSearch(StaticLiveServerTestCase):

    def setUp(self):
        self.dentist = User.objects.create_user(
            username="dentistsel", password="dentpass",
            first_name="Иван", last_name="Врачов"
        )
        self.dentist.profile.role = 'dentist'
        self.dentist.profile.save()
        self.patient = Patient.objects.create(
            full_name="Поисков Тест",
            birth_date="2000-01-01",
            gender='M',
            phone="111111"
        )
        app = Appointment.objects.create(
            patient=self.patient,
            doctor=self.dentist,
            datetime="2026-07-01 10:00"
        )
        Visit.objects.create(
            appointment=app,
            patient=self.patient,
            doctor=self.dentist
        )

    def _login(self, username, password):
        self.driver.get(self.live_server_url + '/login/')
        wait = WebDriverWait(self.driver, 5)
        wait.until(EC.element_to_be_clickable((By.NAME, "username"))).send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        WebDriverWait(self.driver, 5).until(EC.url_contains("/doctor/dashboard/"))

    def test_search_by_patient_name(self):
        """Поиск по имени пациента возвращает соответствующую запись в таблице результатов."""
        # Arrange
        self._login("dentistsel", "dentpass")
        wait = WebDriverWait(self.driver, 5)

        # Act
        self.driver.get(self.live_server_url + '/admin_panel/doctor/search/')
        name_input = wait.until(EC.element_to_be_clickable((By.NAME, "patient_name")))
        name_input.send_keys("Поисков")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # Assert
        wait.until(EC.presence_of_element_located((By.XPATH, "//td[contains(text(),'Поисков')]")))
        assert "Поисков" in self.driver.page_source

    def test_filter_by_doctor(self):
        """Фильтрация по врачу отображает только визиты, связанные с выбранным доктором."""
        # Arrange
        self._login("dentistsel", "dentpass")
        wait = WebDriverWait(self.driver, 5)

        # Act
        self.driver.get(self.live_server_url + '/admin_panel/doctor/search/')
        doctor_select = wait.until(EC.element_to_be_clickable((By.NAME, "doctor")))
        select = Select(doctor_select)
        select.select_by_visible_text(self.dentist.get_full_name())
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # Assert
        wait.until(EC.presence_of_element_located((By.XPATH, "//td[contains(text(),'Поисков')]")))
