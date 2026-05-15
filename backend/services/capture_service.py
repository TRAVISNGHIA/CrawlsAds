import os
import time
from selenium.webdriver.remote.webdriver import WebDriver
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)


def capture_full_page_screenshot(driver: WebDriver, path: str) -> bool:
    """Capture a full page screenshot and save to path."""
    try:
        if settings.CAPTURE_FULLPAGE:
            # Scroll to get full page height
            total_height = driver.execute_script("return document.body.scrollHeight")
            driver.set_window_size(driver.get_window_size()["width"], total_height)
            time.sleep(0.5)

        os.makedirs(os.path.dirname(path), exist_ok=True)
        driver.save_screenshot(path)
        logger.info(f"Screenshot saved: {path}")
        return True
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        return False


def capture_element_screenshot(driver: WebDriver, element, path: str) -> bool:
    """Capture screenshot of a specific element."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        element.screenshot(path)
        logger.info(f"Element screenshot saved: {path}")
        return True
    except Exception as e:
        logger.warning(f"Element screenshot failed: {e}")
        return False


def save_html_snapshot(driver: WebDriver, path: str) -> bool:
    """Save current page HTML to file."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        html = driver.page_source
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"HTML snapshot saved: {path}")
        return True
    except Exception as e:
        logger.error(f"HTML snapshot failed: {e}")
        return False
