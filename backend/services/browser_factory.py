import undetected_chromedriver as uc

from core.logger import get_logger
from services.device_emulation import get_device_config

logger = get_logger(__name__)


def create_browser(
    device: str,
    profile_name: str,
):

    dev = get_device_config(device)

    logger.info(
        f"🌐 Create browser | "
        f"device={device} | "
        f"profile={profile_name}"
    )

    options = uc.ChromeOptions()
    options.add_argument("--user-data-dir=/home/nghia/.config/google-chrome-clone")
    options.add_argument(f"--profile-directory={profile_name}")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-crash-reporter")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=vi-VN")
    options.add_argument("--password-store=basic")
    options.add_argument("--use-mock-keychain")
    options.add_argument(f"--window-size={dev.width},{dev.height}")
    options.add_argument(f"--user-agent={dev.user_agent}")

    if dev.mobile:

        options.add_argument(
            "--touch-events=enabled"
        )

        mobile_emulation = {
            "deviceMetrics": {
                "width": dev.width,
                "height": dev.height,
                "pixelRatio": dev.pixel_ratio,
            },
            "userAgent": dev.user_agent,
        }

        options.add_experimental_option(
            "mobileEmulation",
            mobile_emulation,
        )

    driver = uc.Chrome(
        options=options,
        use_subprocess=True,
        version_main=147,
    )

    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
    """)

    logger.info(
        f"✅ Browser created | "
        f"device={device} | "
        f"profile={profile_name}"
    )

    return driver
