import os
import shutil
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

LOCK_FILES = ["SingletonLock", "SingletonCookie", "SingletonSocket"]


def get_profile_dir(profile_name: str) -> str:
    """
    Returns a cloned profile directory to avoid lock conflicts.
    If CHROME_PROFILE_ROOT is set, clones the named profile.
    Otherwise, creates a fresh temporary directory.
    """
    clone_root = settings.CHROME_PROFILE_CLONE_ROOT
    os.makedirs(clone_root, exist_ok=True)

    clone_path = os.path.join(clone_root, f"profile_{profile_name}")

    if settings.CHROME_PROFILE_ROOT:
        source_profile = os.path.join(settings.CHROME_PROFILE_ROOT, profile_name)
        if os.path.isdir(source_profile):
            if not os.path.exists(clone_path):
                logger.info(f"Cloning profile '{profile_name}' to {clone_path}")
                shutil.copytree(source_profile, clone_path)
            else:
                logger.info(f"Using existing clone for profile '{profile_name}'")
        else:
            logger.warning(f"Profile source not found: {source_profile}, using fresh dir")
            os.makedirs(clone_path, exist_ok=True)
    else:
        os.makedirs(clone_path, exist_ok=True)

    _clean_lock_files(clone_path)
    return clone_path


def _clean_lock_files(profile_dir: str):
    """Remove Chrome singleton lock files that prevent reuse."""
    for lock_file in LOCK_FILES:
        lock_path = os.path.join(profile_dir, lock_file)
        if os.path.exists(lock_path):
            try:
                os.remove(lock_path)
                logger.debug(f"Removed lock file: {lock_path}")
            except Exception as e:
                logger.warning(f"Could not remove lock file {lock_path}: {e}")
