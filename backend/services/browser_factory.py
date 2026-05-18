import undetected_chromedriver as uc

from core.config import settings
from core.logger import get_logger
from services.device_emulation import get_device_config, DeviceConfig
from services.profile_manager import seed_profile_if_needed

logger = get_logger(__name__)


def create_browser(device_name: str, profile_name: str, headless: bool = False):
    """
    Tạo Chrome instance với profile clone 2 lớp:
      --user-data-dir  = clone_root  (CHROME_PROFILE_CLONE_ROOT/profile_name)
      --profile-directory = profile_name
    """
    device = get_device_config(device_name)
    clone_root = seed_profile_if_needed(profile_name)

    options = uc.ChromeOptions()

    # ── Stability ──
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=0")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-infobars")

    # ── Stealth — ẩn dấu hiệu bot ──
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-web-security")

    # ── Profile ──
    options.add_argument(f"--window-size={device.width},{device.height}")
    options.add_argument(f"--user-data-dir={clone_root}")
    options.add_argument(f"--profile-directory={profile_name}")
    options.add_argument(f"--user-agent={device.user_agent}")

    # ── Ngôn ngữ tiếng Việt ──
    options.add_argument("--lang=vi-VN")
    options.add_argument("--accept-lang=vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7")

    if headless:
        options.add_argument("--headless=new")

    if settings.CHROME_BINARY:
        options.binary_location = settings.CHROME_BINARY

    try:
        driver = uc.Chrome(
            options=options,
            version_main=147,
            use_subprocess=True,
        )

        driver.set_page_load_timeout(45)
        driver.set_script_timeout(30)

        # ── Xóa dấu hiệu webdriver qua CDP ──
        _apply_stealth(driver, device)

        if device.mobile:
            _apply_mobile_emulation(driver, device)

        logger.info(
            f"Browser created | device={device_name}, profile={profile_name}, "
            f"headless={headless}, user_data_dir={clone_root}"
        )
        return driver

    except Exception as e:
        logger.error(f"Failed to create browser: {e}")
        raise


def _apply_stealth(driver, device: DeviceConfig):
    """Inject script ẩn webdriver fingerprint ngay khi page load."""
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                // Ẩn navigator.webdriver
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

                // Giả lập plugins như trình duyệt thật
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });

                // Ngôn ngữ
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['vi-VN', 'vi', 'en-US', 'en'],
                });

                // Xóa chrome.runtime dấu hiệu automation
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {},
                };

                // Che permission query
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications'
                        ? Promise.resolve({ state: Notification.permission })
                        : originalQuery(parameters)
                );
            """
        })
    except Exception as e:
        logger.warning(f"Stealth script failed (non-fatal): {e}")


def _apply_mobile_emulation(driver, device: DeviceConfig):
    """Áp dụng emulation mobile/tablet qua Chrome DevTools Protocol."""
    try:
        driver.execute_cdp_cmd("Network.enable", {})

        driver.execute_cdp_cmd(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": device.width,
                "height": device.height,
                "deviceScaleFactor": device.scale_factor,
                "mobile": device.mobile,
            },
        )

        driver.execute_cdp_cmd(
            "Emulation.setUserAgentOverride",
            {"userAgent": device.user_agent},
        )

        if device.mobile:
            driver.execute_cdp_cmd(
                "Emulation.setTouchEmulationEnabled",
                {"enabled": True, "maxTouchPoints": 5},
            )

        logger.debug(f"Mobile emulation: {device.width}x{device.height}, dpr={device.scale_factor}")

    except Exception as e:
        logger.warning(f"CDP mobile emulation failed (non-fatal): {e}")