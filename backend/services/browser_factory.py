import undetected_chromedriver as uc

def create_browser(device: str, profile_name: str):
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--lang=vi-VN")
    options.add_argument("--user-data-dir=/home/nghia/.config/google-chrome-clone")
    options.add_argument(f"--profile-directory={profile_name}")

    options.add_argument("--password-store=basic")
    options.add_argument("--use-mock-keychain")

    driver = uc.Chrome(options=options, use_subprocess=True, version_main=147)
    return driver