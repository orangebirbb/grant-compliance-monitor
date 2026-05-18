import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os

BASE_URL = "http://127.0.0.1:8080"

@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

# --- Test 1: Page loads ---
def test_page_loads(driver):
    driver.get(BASE_URL)
    assert "Grant Compliance Monitor" in driver.title
    print("✅ Test 1 passed: Page loads correctly")

# --- Test 2: Header visible ---
def test_header_visible(driver):
    driver.get(BASE_URL)
    header = driver.find_element(By.TAG_NAME, "h1")
    assert header.is_displayed()
    assert "Grant Compliance Monitor" in header.text
    print("✅ Test 2 passed: Header is visible")

# --- Test 3: Upload area visible ---
def test_upload_area_visible(driver):
    driver.get(BASE_URL)
    upload = driver.find_element(By.CLASS_NAME, "upload-area")
    assert upload.is_displayed()
    print("✅ Test 3 passed: Upload area is visible")

# --- Test 4: Submit button present ---
def test_submit_button_present(driver):
    driver.get(BASE_URL)
    button = driver.find_element(By.ID, "submitBtn")
    assert button.is_displayed()
    assert button.is_enabled()
    print("✅ Test 4 passed: Submit button is present")

# --- Test 5: Error shows on empty submit ---
def test_empty_submit_shows_error(driver):
    driver.get(BASE_URL)
    button = driver.find_element(By.ID, "submitBtn")
    button.click()
    error = driver.find_element(By.ID, "errorMsg")
    assert error.is_displayed()
    print("✅ Test 5 passed: Error shows on empty submit")

# --- Test 6: Background color correct ---
def test_background_color(driver):
    driver.get(BASE_URL)
    body = driver.find_element(By.TAG_NAME, "body")
    bg = driver.execute_script(
        "return window.getComputedStyle(arguments[0]).backgroundColor;", body
    )
    assert bg == "rgb(255, 245, 240)"
    print("✅ Test 6 passed: Correct orange background")

# --- Test 7: Pipeline badge visible ---
def test_pipeline_badge_visible(driver):
    driver.get(BASE_URL)
    badge = driver.find_element(By.CLASS_NAME, "badge")
    assert badge.is_displayed()
    assert "4-Agent Pipeline" in badge.text
    print("✅ Test 7 passed: Pipeline badge visible")

# --- Test 8: Results hidden on load ---
def test_results_hidden_on_load(driver):
    driver.get(BASE_URL)
    results = driver.find_element(By.ID, "results")
    assert not results.is_displayed()
    print("✅ Test 8 passed: Results hidden on page load")

# --- Test 9: Loading spinner hidden on load ---
def test_loading_hidden_on_load(driver):
    driver.get(BASE_URL)
    loading = driver.find_element(By.ID, "loading")
    assert not loading.is_displayed()
    print("✅ Test 9 passed: Loading spinner hidden on load")

# --- Test 10: Page has correct title tag ---
def test_page_title(driver):
    driver.get(BASE_URL)
    assert driver.title == "Grant Compliance Monitor"
    print("✅ Test 10 passed: Page title is correct")