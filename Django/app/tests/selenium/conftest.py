import pytest
from unittest.mock import patch
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


@pytest.fixture(autouse=True)
def mock_fastapi_available():
    """Bypass FastAPI availability check so login works in selenium tests."""
    with patch("app.utils.is_fastapi_available", return_value=True), \
         patch("app.services.fastapi_health.get_fastapi_status",
               return_value={"available": True, "url": "http://localhost:9999",
                             "error": None, "response_time_ms": 0, "status_code": 200}):
        yield


@pytest.fixture
def chrome_driver(request):
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    request.instance.driver = driver
    yield driver
    driver.quit()
