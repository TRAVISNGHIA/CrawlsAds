from dataclasses import dataclass


@dataclass
class DeviceConfig:
    name: str
    width: int
    height: int
    pixel_ratio: float
    mobile: bool
    user_agent: str

DEVICES = {
    "desktop": DeviceConfig(
        name="desktop",
        width=1366,
        height=768,
        pixel_ratio=1.0,
        mobile=False,
        user_agent=(
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/147.0.0.0 "
            "Safari/537.36"
        ),
    ),

    "mobile": DeviceConfig(
        name="mobile",
        width=390,
        height=844,
        pixel_ratio=3.0,
        mobile=True,
        user_agent=(
            "Mozilla/5.0 "
            "(Linux; Android 14; Pixel 7) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/147.0.0.0 "
            "Mobile Safari/537.36"
        ),
    ),
    "tablet": DeviceConfig(
        name="tablet",
        width=820,
        height=1180,
        pixel_ratio=2.0,
        mobile=True,
        user_agent=(
            "Mozilla/5.0 "
            "(Linux; Android 14; SM-X716B) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/147.0.0.0 "
            "Safari/537.36"
        ),
    ),
}

def get_device_config(
    device_name: str,
) -> DeviceConfig:

    if not device_name:
        return DEVICES["desktop"]

    return DEVICES.get(
        device_name.lower(),
        DEVICES["desktop"],
    )

