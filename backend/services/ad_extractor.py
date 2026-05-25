import time
import random
from urllib.parse import quote_plus
from typing import List, Dict, Any, Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from core.logger import get_logger
from services.url_resolver import resolve_final_url, extract_domain, clean_url

logger = get_logger(__name__)

SPONSORED_LABELS = [
    "Sponsored",
    "Quảng cáo",
    "Được tài trợ",
    "Ad",
]

GOOGLE_SEARCH_URL = "https://www.google.com.vn/search?q={query}&hl=vi&gl=vn"

CAPTCHA_SIGNALS = [
    "google.com/sorry",
    "recaptcha",
    "captcha",
    "unusual traffic",
    "lưu lượng truy cập bất thường",
    "automated queries",
]


def search_and_extract_ads(
    driver: WebDriver,
    keyword: str,
    run_id: str,
    device: str,
    profile_name: str,
) -> List[Dict[str, Optional[str]]]:

    try:
        logger.info(f"Searching keyword: {keyword}")

        search_url = GOOGLE_SEARCH_URL.format(
            query=quote_plus(keyword)
        )

        driver.get(search_url)

        time.sleep(random.uniform(3, 5))

        logger.info(f"Current URL: {driver.current_url}")

        if _is_captcha_page(driver):
            logger.warning(f"Google CAPTCHA detected for '{keyword}'")

            _try_screenshot_captcha(
                driver,
                run_id,
                keyword,
                device
            )

            return []

        _human_scroll(driver)

        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//span[text()='Quảng cáo' or text()='Sponsored' or text()='Được tài trợ' or text()='Ad']"
                    )
                )
            )
        except TimeoutException:
            logger.info(f"No sponsored label found for '{keyword}'")

        ads = _extract_ads_from_page(
            driver,
            keyword,
            run_id,
            device,
            profile_name
        )

        logger.info(f"Found {len(ads)} ads for '{keyword}'")

        return ads

    except Exception as e:
        logger.error(f"Search failed for '{keyword}': {e}")
        return []


def _is_captcha_page(driver: WebDriver) -> bool:
    current_url = driver.current_url.lower()
    page_source = driver.page_source.lower()

    for signal in CAPTCHA_SIGNALS:
        if signal in current_url or signal in page_source:
            return True

    return False


def _try_screenshot_captcha(driver: WebDriver, run_id: str, keyword: str, device: str):
    try:
        import os
        from core.config import settings

        safe_kw = keyword.replace(" ", "_")[:30]

        path = os.path.join(
            settings.SCREENSHOTS_DIR,
            f"CAPTCHA_{run_id}_{safe_kw}_{device}.png"
        )

        driver.save_screenshot(path)

        logger.info(f"CAPTCHA screenshot saved: {path}")

    except Exception:
        pass


def _human_scroll(driver: WebDriver):
    try:
        scroll_distance = random.randint(200, 500)

        driver.execute_script(
            f"window.scrollTo(0, {scroll_distance});"
        )

        time.sleep(random.uniform(0.3, 0.8))

        driver.execute_script("window.scrollTo(0, 0);")

        time.sleep(random.uniform(0.2, 0.5))

    except Exception:
        pass


def _extract_ads_from_page(
    driver: WebDriver,
    keyword: str,
    run_id: str,
    device: str,
    profile_name: str,
) -> List[Dict[str, Any]]:

    ads = []

    ad_blocks = driver.find_elements(
        By.XPATH,
        "//span[text()='Quảng cáo' or text()='Sponsored' or text()='Được tài trợ' or text()='Ad']"
        "/ancestor::div[@data-text-ad]"
    )

    if not ad_blocks:
        ad_blocks = driver.find_elements(
            By.XPATH,
            "//span[text()='Quảng cáo' or text()='Sponsored' or text()='Được tài trợ' or text()='Ad']"
            "/ancestor::div[1]"
        )

    if not ad_blocks:
        tads = driver.find_elements(By.CSS_SELECTOR, "#tads > div")

        if tads:
            ad_blocks = tads

    if not ad_blocks:
        logger.info(f"No ad blocks found for '{keyword}'")
        return []

    for position, block in enumerate(ad_blocks, start=1):
        try:
            ad_data = _parse_ad_block(
                block,
                position,
                keyword,
                run_id,
                device,
                profile_name
            )

            if ad_data:
                ads.append(ad_data)

        except Exception as e:
            logger.warning(
                f"Error parsing ad block position {position}: {e}"
            )

    return ads


def _parse_ad_block(
    block,
    position: int,
    keyword: str,
    run_id: str,
    device: str,
    profile_name: str,
) -> Optional[Dict[str, Any]]:

    try:
        if not block.text.strip():
            return None

        ad_title = _extract_title(block)

        if not ad_title:
            return None

        raw_url = _extract_href(block)

        advertiser = _extract_advertiser(block)

        visible_domain = _extract_visible_domain(block)

        final_url = None
        final_domain = None

        if raw_url:
            try:
                final_url = resolve_final_url(
                    raw_url,
                    timeout=6
                )

                final_domain = extract_domain(final_url)

            except Exception:
                final_url = raw_url
                final_domain = extract_domain(raw_url)

        if not visible_domain and final_domain:
            visible_domain = final_domain

        return {
            "run_id": run_id,
            "keyword": keyword,
            "device": device,
            "profile_name": profile_name,
            "has_ads": True,
            "ad_position": position,
            "ad_title": ad_title,
            "advertiser": advertiser,
            "visible_domain": visible_domain,
            "raw_url": clean_url(raw_url),
            "final_url": final_url,
            "final_domain": final_domain,
        }

    except Exception as e:
        logger.warning(f"Failed to parse ad block: {e}")
        return None


def _extract_title(block) -> Optional[str]:

    for sel in ["h3", "h2", "[role='heading']"]:

        try:
            els = block.find_elements(By.CSS_SELECTOR, sel)

            for el in els:
                text = el.text.strip()

                if text and len(text) > 3:
                    return text[:200]

        except Exception:
            continue

    lines = [
        l.strip()
        for l in block.text.split("\n")
        if l.strip()
    ]

    return lines[0][:200] if lines else None


def _extract_href(block) -> Optional[str]:

    try:
        links = block.find_elements(
            By.CSS_SELECTOR,
            "a[href]"
        )

        for link in links:
            href = link.get_attribute("href")

            if (
                href
                and href.startswith("http")
                and "google.com/search" not in href
            ):
                return href

    except Exception:
        pass

    return None


def _extract_advertiser(block) -> Optional[str]:

    try:
        for sel in [
            "span.x2VHCd",
            ".yCgKKc",
            ".vNuEHb",
            "span[data-dtld]"
        ]:

            els = block.find_elements(By.CSS_SELECTOR, sel)

            for el in els:
                text = el.text.strip()

                if text:
                    return text[:100]

    except Exception:
        pass

    return None


def _extract_visible_domain(block) -> Optional[str]:

    try:
        for sel in [
            "span.qzEoUe",
            ".VDgVie",
            "cite",
            ".UdQCqe"
        ]:

            els = block.find_elements(By.CSS_SELECTOR, sel)

            for el in els:
                text = el.text.strip()

                if text and "." in text:
                    return text[:100]

    except Exception:
        pass

    return None