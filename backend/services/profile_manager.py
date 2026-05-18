import os
import glob
import shutil

from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

LOCK_FILES = ["SingletonLock", "SingletonCookie", "SingletonSocket"]

IGNORE_PATTERNS = [
    "Singleton*",
    ".com.google.Chrome.*",
    "BrowserMetrics",
    "lockfile",
    "*.lock",
    "*.tmp",
    "Crashpad",
    "Code Cache",
    "GPUCache",
    "ShaderCache",
    "GrShaderCache",
]

def profile_src_dir(profile_name: str) -> str:
    return os.path.join(settings.CHROME_PROFILE_ROOT, profile_name)


def profile_clone_root(profile_name: str) -> str:
    return os.path.join(settings.CHROME_PROFILE_CLONE_ROOT, profile_name)


def profile_clone_dir(profile_name: str) -> str:
    return os.path.join(profile_clone_root(profile_name), profile_name)

def seed_profile_if_needed(profile_name: str) -> str:
    src = profile_src_dir(profile_name)
    clone_root = profile_clone_root(profile_name)
    clone_dir = profile_clone_dir(profile_name)

    if not os.path.isdir(src):
        raise FileNotFoundError(
            f"Profile gốc không tồn tại: {src}\n"
            f"Kiểm tra CHROME_PROFILE_ROOT trong .env"
        )

    if not os.path.isdir(clone_dir):
        logger.info(f"Clone chưa có → đang copy: {src} → {clone_dir}")
        os.makedirs(clone_root, exist_ok=True)

        shutil.copytree(
            src,
            clone_dir,
            ignore=shutil.ignore_patterns(*IGNORE_PATTERNS),
            dirs_exist_ok=True,
        )
        logger.info(f"Clone hoàn tất: {clone_dir}")
    else:
        logger.info(f"Clone đã tồn tại, giữ nguyên session: {clone_dir}")

    cleanup_singletons(clone_root)

    return clone_root


def cleanup_singletons(root_dir: str):
    for p in glob.glob(os.path.join(root_dir, "**", "Singleton*"), recursive=True):
        try:
            os.remove(p)
            logger.debug(f"Removed: {p}")
        except Exception as e:
            logger.warning(f"Không xóa được {p}: {e}")

    for p in glob.glob(os.path.join(root_dir, "**", "lockfile"), recursive=True):
        try:
            os.remove(p)
            logger.debug(f"Removed: {p}")
        except Exception as e:
            logger.warning(f"Không xóa được {p}: {e}")