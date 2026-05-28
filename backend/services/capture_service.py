import time
import base64
from selenium.webdriver.remote.webdriver import WebDriver

from core.logger import get_logger

logger = get_logger(__name__)


def capture_full_page_screenshot(driver: WebDriver, output_path: str):
    try:
        time.sleep(1)

        # ✅ Dùng CDP để chụp full page — không cần set_window_size (tránh crash Chrome)
        result = driver.execute_cdp_cmd(
            "Page.captureScreenshot",
            {
                "format": "png",
                "captureBeyondViewport": True,  # chụp toàn bộ trang, kể cả phần cuộn
                "clip": None,
            },
        )

        img_data = base64.b64decode(result["data"])

        with open(output_path, "wb") as f:
            f.write(img_data)

        logger.info(f"Screenshot saved: {output_path}")

    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        # ── Fallback: chụp viewport thông thường nếu CDP thất bại ──
        try:
            driver.save_screenshot(output_path)
            logger.info(f"Screenshot saved (fallback): {output_path}")
        except Exception as e2:
            logger.error(f"Screenshot fallback also failed: {e2}")


def save_html_snapshot(driver: WebDriver, output_path: str):
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        logger.info(f"HTML snapshot saved: {output_path}")

    except Exception as e:
        logger.error(f"Save HTML failed: {e}")