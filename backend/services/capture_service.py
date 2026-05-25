import time
from selenium.webdriver.remote.webdriver import WebDriver

from core.logger import get_logger

logger = get_logger(__name__)


def capture_full_page_screenshot(
    driver: WebDriver,
    output_path: str,
):
    try:
        time.sleep(2)

        # scroll top
        driver.execute_script(
            "window.scrollTo(0, 0);"
        )

        time.sleep(1)

        total_width = driver.execute_script(
            "return document.body.scrollWidth"
        )

        total_height = driver.execute_script(
            "return document.body.scrollHeight"
        )

        # giới hạn tránh crash chrome
        total_width = min(total_width, 1920)
        total_height = min(total_height, 15000)

        driver.set_window_size(
            total_width,
            total_height
        )

        time.sleep(2)

        success = driver.save_screenshot(output_path)

        if success:
            logger.info(
                f"Screenshot saved: {output_path}"
            )
        else:
            logger.warning(
                f"Screenshot save returned false: {output_path}"
            )

    except Exception as e:
        logger.error(f"Screenshot failed: {e}")


def save_html_snapshot(
    driver: WebDriver,
    output_path: str,
):
    try:
        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(driver.page_source)

        logger.info(
            f"HTML snapshot saved: {output_path}"
        )

    except Exception as e:
        logger.error(
            f"Save HTML failed: {e}"
        )