import re
import requests
from urllib.parse import urlparse, parse_qs, unquote
from core.logger import get_logger

logger = get_logger(__name__)

REDIRECT_PARAMS = ["adurl", "url", "q", "dest", "redirect"]
GOOGLE_REDIRECT_PATHS = ["/aclk", "/url"]


def is_google_redirect(url: str) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    return "google." in parsed.netloc and parsed.path in GOOGLE_REDIRECT_PATHS


def extract_from_google_redirect(url: str) -> str:
    """Extract final URL from Google redirect parameters."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    for param in REDIRECT_PARAMS:
        if param in params:
            extracted = unquote(params[param][0])
            logger.debug(f"Extracted from '{param}': {extracted}")
            return extracted
    return url


def resolve_final_url(url: str, timeout: int = 8) -> str:
    """
    Follow redirects to find the final landing URL.
    Handles Google redirect links first, then HTTP redirects.
    """
    if not url:
        return url

    if is_google_redirect(url):
        url = extract_from_google_redirect(url)

    try:
        resp = requests.head(
            url,
            allow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0"},
        )
        final = resp.url
        logger.debug(f"Resolved {url} -> {final}")
        return final
    except requests.exceptions.TooManyRedirects:
        logger.warning(f"Too many redirects for {url}")
        return url
    except Exception as e:
        logger.warning(f"URL resolution failed for {url}: {e}")
        return url


def extract_domain(url: str) -> str:
    """Extract clean domain from URL."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def clean_url(url: str) -> str:
    """Remove UTM and tracking parameters for display."""
    if not url:
        return ""
    try:
        # Return URL as-is but unquoted
        return unquote(url)
    except Exception:
        return url
