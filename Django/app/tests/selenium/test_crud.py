import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from app.models import Patient

@pytest.mark.selenium
@pytest.mark.usefixtures("chrome_driver")
class TestCRUD(StaticLiveServerTestCase):

    def setUp(self):
        self.admin_user = User.objects.create_superuser(username="admin_sel", password="adminpass")
        self.admin_user.profile.role = 'admin'
        self.admin_user.profile.save()

    def _login(self, username, password, wait_url):
        self.driver.get(self.live_server_url + '/login/')
        wait = WebDriverWait(self.driver, 5)
        wait.until(EC.element_to_be_clickable((By.NAME, "username"))).send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        WebDriverWait(self.driver, 5).until(EC.url_contains(wait_url))

    def test_create_service(self):
        """Администратор успешно создаёт новую услугу, и она появляется в списке услуг."""
        # Arrange
        self._login("admin_sel", "adminpass", "/admin/dashboard/")
        wait = WebDriverWait(self.driver, 5)

        # Act
        self.driver.get(self.live_server_url + '/admin_panel/admin/services/')
        add_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Добавить услугу")))
        add_link.click()
        code_field = wait.until(EC.element_to_be_clickable((By.NAME, "code")))
        code_field.send_keys("TEST01")
        self.driver.find_element(By.NAME, "name").send_keys("Тестовая услуга")
        self.driver.find_element(By.NAME, "cost").send_keys("999")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # Assert
        wait.until(EC.presence_of_element_located((By.XPATH, "//td[contains(text(),'TEST01')]")))
        assert "TEST01" in self.driver.page_source

    def test_edit_patient(self):
        """Менеджер редактирует данные пациента, и изменения сохраняются в списке пациентов."""
        # Arrange
        patient = Patient.objects.create(
            full_name="Селениумов Тест",
            birth_date="1990-01-01",
            gender='M',
            phone="123456"
        )
        manager = User.objects.create_user(username="managersel", password="manpass")
        manager.profile.role = 'manager'
        manager.profile.save()
        self._login("managersel", "manpass", "/manager/dashboard/")
        wait = WebDriverWait(self.driver, 5)

        # Act
        self.driver.get(self.live_server_url + '/admin_panel/manager/patients/')
        edit_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[title='Редактировать']")))
        edit_link.click()
        # Explicitly fill all required fields so form validation passes
        full_name = wait.until(EC.element_to_be_clickable((By.NAME, "full_name")))
        full_name.clear()
        full_name.send_keys("Селениумов Тест")
        birth = self.driver.find_element(By.NAME, "birth_date")
        birth.clear()
        birth.send_keys("1990-01-01 00:00:00")
        phone_input = self.driver.find_element(By.NAME, "phone")
        phone_input.clear()
        phone_input.send_keys("9998887766")
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        # Assert
        wait.until(EC.presence_of_element_located((By.XPATH, "//td[contains(text(),'9998887766')]")))
        assert "9998887766" in self.driver.page_source
