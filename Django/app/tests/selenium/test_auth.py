import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User

@pytest.mark.selenium
@pytest.mark.usefixtures("chrome_driver")
class TestAuth(StaticLiveServerTestCase):

    def test_register_new_user(self):
        """Новый пользователь успешно регистрируется и перенаправляется на страницу логина."""
        # Arrange
        wait = WebDriverWait(self.driver, 5)

        # Act
        self.driver.get(self.live_server_url + '/register/')
        username = wait.until(EC.element_to_be_clickable((By.NAME, "username")))
        username.send_keys("seleniumuser")
        self.driver.find_element(By.NAME, "email").send_keys("sel@test.com")
        self.driver.find_element(By.NAME, "first_name").send_keys("Selenium")
        self.driver.find_element(By.NAME, "last_name").send_keys("Test")
        self.driver.find_element(By.NAME, "password1").send_keys("TestPass123!")
        self.driver.find_element(By.NAME, "password2").send_keys("TestPass123!")
        submit = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit.click()

        # Assert
        wait.until(EC.url_contains("/login/"))
        assert "login" in self.driver.current_url

    def test_login_logout(self):
        """Зарегистрированный пользователь входит в систему и успешно выходит из неё."""
        # Arrange
        u = User.objects.create_user(username="logintest", password="loginpass")
        u.profile.role = 'dentist'
        u.profile.save()
        wait = WebDriverWait(self.driver, 5)

        # Act
        self.driver.get(self.live_server_url + '/login/')
        username = wait.until(EC.element_to_be_clickable((By.NAME, "username")))
        username.send_keys("logintest")
        self.driver.find_element(By.NAME, "password").send_keys("loginpass")
        submit = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit.click()
        # default role is 'dentist' → redirects to /admin_panel/doctor/dashboard/
        wait.until(EC.url_contains("/doctor/dashboard/"))
        logout_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='logout']")))
        logout_link.click()

        # Assert
        wait.until(EC.url_contains("/login/"))

    def test_access_protected_page_anonymous(self):
        """Анонимный пользователь при обращении к защищённой странице перенаправляется на логин."""
        # Arrange
        wait = WebDriverWait(self.driver, 5)

        # Act
        self.driver.get(self.live_server_url + '/admin_panel/doctor/dashboard/')

        # Assert
        wait.until(EC.url_contains("/login/"))
