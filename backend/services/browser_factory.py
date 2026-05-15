import time
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from core.config import settings
from core.logger import get_logger
from services.device_emulation import get_device_config, DeviceConfig
from services.profile_manager import get_profile_dir

logger = get_logger(__name__)


def create_browser(device_name: str, profile_name: str, headless: bool = False):
    """Create and return a configured undetected Chrome browser instance."""
    device = get_device_config(device_name)
    profile_dir = get_profile_dir(profile_name)

    options = uc.ChromeOptions()

    # Core stability options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--window-size={device.width},{device.height}")
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument(f"--user-agent={device.user_agent}")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")
    options.add_argument("--lang=vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7")

    if headless:
        options.add_argument("--headless=new")

    # Set Chrome binary if specified
    if settings.CHROME_BINARY:
        options.binary_location = settings.CHROME_BINARY

    try:
        driver = uc.Chrome(options=options, use_subprocess=True)
        driver.set_page_load_timeout(45)
        driver.set_script_timeout(30)

        # Apply mobile emulation via CDP
        if device.mobile:
            _apply_mobile_emulation(driver, device)

        logger.info(f"Browser created: device={device_name}, profile={profile_name}, headless={headless}")
        return driver
    except Exception as e:
        logger.error(f"Failed to create browser: {e}")
        raise


def _apply_mobile_emulation(driver, device: DeviceConfig):
    """Use Chrome DevTools Protocol to simulate mobile device."""
    try:
        driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
            "width": device.width,
            "height": device.height,
            "deviceScaleFactor": device.scale_factor,
            "mobile": device.mobile,
        })
        driver.execute_cdp_cmd("Emulation.setUserAgentOverride", {
            "userAgent": device.user_agent,
        })
        logger.debug(f"Mobile emulation applied: {device.width}x{device.height}")
    except Exception as e:
        logger.warning(f"CDP mobile emulation failed (non-fatal): {e}")
