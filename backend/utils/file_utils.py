import os
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)


def ensure_storage_dirs():
    """Create storage directories if they don't exist."""
    os.makedirs(settings.SCREENSHOTS_DIR, exist_ok=True)
    os.makedirs(settings.HTML_DIR, exist_ok=True)
    logger.info(f"Storage dirs ready: {settings.BASE_DIR}/storage/")


def get_screenshot_path(run_id: str, keyword: str, device: str, position: int = 0) -> str:
    safe_kw = keyword.replace(" ", "_").replace("/", "-")[:50]
    filename = f"{run_id}_{safe_kw}_{device}_{position}.png"
    return os.path.join(settings.SCREENSHOTS_DIR, filename)


def get_html_path(run_id: str, keyword: str, device: str) -> str:
    safe_kw = keyword.replace(" ", "_").replace("/", "-")[:50]
    filename = f"{run_id}_{safe_kw}_{device}.html"
    return os.path.join(settings.HTML_DIR, filename)


def relative_storage_path(full_path: str) -> str:
    """Convert absolute path to a path relative to backend/storage/."""
    if not full_path:
        return full_path
    try:
        return os.path.relpath(full_path, settings.BASE_DIR)
    except Exception:
        return full_path
