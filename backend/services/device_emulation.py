from dataclasses import dataclass
from typing import Optional

@dataclass
class DeviceConfig:
    name: str
    width: int
    height: int
    scale_factor: float
    mobile: bool
    user_agent: str


DEVICES = {
    "desktop": DeviceConfig(
        name="desktop",
        width=1366,
        height=768,
        scale_factor=1.0,
        mobile=False,
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    ),
    "mobile": DeviceConfig(
        name="mobile",
        width=390,
        height=844,
        scale_factor=3.0,
        mobile=True,
        user_agent=(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.0 Mobile/15E148 Safari/604.1"
        ),
    ),
    "tablet": DeviceConfig(
        name="tablet",
        width=768,
        height=1024,
        scale_factor=2.0,
        mobile=True,
        user_agent=(
            "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.0 Mobile/15E148 Safari/604.1"
        ),
    ),
}


def get_device_config(device_name: str) -> DeviceConfig:
    return DEVICES.get(device_name.lower(), DEVICES["desktop"])
