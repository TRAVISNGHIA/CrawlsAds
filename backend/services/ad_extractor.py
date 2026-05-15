import time
from typing import List, Dict, Any, Optional
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.logger import get_logger
from services.url_resolver import resolve_final_url, extract_domain, clean_url

logger = get_logger(__name__)

# All known "sponsored" label texts Google uses
SPONSORED_LABELS = [
    "Sponsored",
    "Ad",
    "Quảng cáo",
    "Được tài trợ",
    "Annonce",
    "Anuncio",
    "Reklam",
    "广告",
]

# CSS selectors for ad containers (Google changes these frequently)
AD_CONTAINER_SELECTORS = [
    "[data-text-ad]",
    "div[aria-label='Ads']",
    "div[aria-label='Ad']",
    "#tads .uEierd",
    "#tads > div",
    ".commercial-unit-desktop-top",
    ".pla-unit",
    "div[data-hveid] > div[data-ved]",
]

GOOGLE_SEARCH_URL = "https://www.google.com/search?q={query}&hl=vi"


def search_and_extract_ads(
    driver: WebDriver,
    keyword: str,
    run_id: str,
    device: str,
    profile_name: str,
) -> List[Dict[str, Any]]:
    """
    Navigate to Google Search for the keyword and extract all ad results.
    Returns a list of ad data dicts.
    """
    url = GOOGLE_SEARCH_URL.format(query=keyword.replace(" ", "+"))
    ads = []

    try:
        logger.info(f"Searching: '{keyword}' on {device}")
        driver.get(url)
        time.sleep(2)  # Let page settle

        # Wait for results container
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
        except Exception:
            logger.warning(f"Search results container not found for '{keyword}'")

        time.sleep(1)
        ads = _extract_ads_from_page(driver, keyword, run_id, device, profile_name)
        logger.info(f"Found {len(ads)} ads for '{keyword}' on {device}")

    except Exception as e:
        logger.error(f"Error searching '{keyword}': {e}")

    return ads


def _extract_ads_from_page(
    driver: WebDriver,
    keyword: str,
    run_id: str,
    device: str,
    profile_name: str,
) -> List[Dict[str, Any]]:
    """Extract ad information from the current search results page."""
    ads = []

    # Strategy 1: Find by sponsored label text
    ad_blocks = _find_ad_blocks_by_label(driver)

    # Strategy 2: Find by known ad container selectors
    if not ad_blocks:
        ad_blocks = _find_ad_blocks_by_selector(driver)

    if not ad_blocks:
        logger.info(f"No ad blocks found for '{keyword}'")
        return []

    for position, block in enumerate(ad_blocks, start=1):
        try:
            ad_data = _parse_ad_block(block, position, keyword, run_id, device, profile_name)
            if ad_data:
                ads.append(ad_data)
        except Exception as e:
            logger.warning(f"Error parsing ad block at position {position}: {e}")

    return ads


def _find_ad_blocks_by_label(driver: WebDriver):
    """Find ad containers by locating sponsored label text."""
    ad_blocks = []
    try:
        # Find all elements containing sponsored text
        for label in SPONSORED_LABELS:
            elements = driver.find_elements(
                By.XPATH, f"//*[contains(text(), '{label}')]"
            )
            for el in elements:
                # Walk up to find the ad container div
                container = _get_ad_container(el)
                if container and container not in ad_blocks:
                    ad_blocks.append(container)
    except Exception as e:
        logger.warning(f"Label-based ad detection failed: {e}")
    return ad_blocks


def _find_ad_blocks_by_selector(driver: WebDriver):
    """Find ad containers using CSS selectors."""
    for selector in AD_CONTAINER_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                logger.debug(f"Found ads via selector: {selector}")
                return elements
        except Exception:
            continue
    return []


def _get_ad_container(element):
    """Walk up DOM tree to find a meaningful ad container."""
    try:
        current = element
        for _ in range(6):
            parent = current.find_element(By.XPATH, "..")
            tag = parent.tag_name.lower()
            if tag in ("body", "html"):
                break
            # Look for divs with some content
            if tag == "div" and len(parent.text) > 20:
                return parent
            current = parent
    except Exception:
        pass
    return element


def _parse_ad_block(
    block,
    position: int,
    keyword: str,
    run_id: str,
    device: str,
    profile_name: str,
) -> Optional[Dict[str, Any]]:
    """Extract structured data from an ad block element."""
    try:
        block_text = block.text.strip()
        if not block_text:
            return None

        # Extract title (usually the first link text or largest heading)
        ad_title = _extract_title(block)
        if not ad_title:
            return None

        # Extract URL
        raw_url = _extract_href(block)
        advertiser = _extract_advertiser(block)
        visible_domain = _extract_visible_domain(block)

        # Resolve final URL
        final_url = None
        final_domain = None
        if raw_url:
            try:
                final_url = resolve_final_url(raw_url, timeout=6)
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
    """Extract the ad headline/title."""
    selectors = ["h3", "h2", "[role='heading']", "a[href]"]
    for sel in selectors:
        try:
            elements = block.find_elements(By.CSS_SELECTOR, sel)
            for el in elements:
                text = el.text.strip()
                if text and len(text) > 3:
                    return text[:200]
        except Exception:
            continue
    # Fallback: first non-empty line
    lines = [l.strip() for l in block.text.split("\n") if l.strip()]
    if lines:
        return lines[0][:200]
    return None


def _extract_href(block) -> Optional[str]:
    """Extract the main link URL from ad block."""
    try:
        links = block.find_elements(By.CSS_SELECTOR, "a[href]")
        for link in links:
            href = link.get_attribute("href")
            if href and href.startswith("http") and "google.com/search" not in href:
                return href
    except Exception:
        pass
    return None


def _extract_advertiser(block) -> Optional[str]:
    """Try to extract advertiser name from ad block."""
    try:
        # Google sometimes shows advertiser in specific spans
        candidates = block.find_elements(By.CSS_SELECTOR, "span.x2VHCd, .yCgKKc, .vNuEHb")
        for el in candidates:
            text = el.text.strip()
            if text:
                return text[:100]
    except Exception:
        pass
    return None


def _extract_visible_domain(block) -> Optional[str]:
    """Extract the displayed domain/URL from ad block."""
    try:
        candidates = block.find_elements(By.CSS_SELECTOR, "span.qzEoUe, .VDgVie, cite, .UdQCqe")
        for el in candidates:
            text = el.text.strip()
            if text and "." in text:
                return text[:100]
    except Exception:
        pass
    return None
