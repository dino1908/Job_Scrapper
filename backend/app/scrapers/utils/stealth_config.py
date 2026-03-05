"""
Stealth configuration for browser automation to avoid detection.
"""


def get_playwright_stealth_config():
    """
    Get Playwright stealth configuration.

    Returns:
        Dictionary of Playwright launch options
    """
    return {
        'headless': True,
        'args': [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--window-size=1920,1080'
        ]
    }


def get_playwright_context_config():
    """
    Get Playwright browser context configuration.

    Returns:
        Dictionary of context options
    """
    return {
        'viewport': {'width': 1920, 'height': 1080},
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'locale': 'en-US',
        'timezone_id': 'America/New_York',
        'permissions': [],
        'geolocation': None,
        'color_scheme': 'light',
        'accept_downloads': False
    }


def get_selenium_options():
    """
    Get Selenium Chrome options with stealth configuration.

    Returns:
        Chrome options object
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()

    # Basic options
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    # Anti-detection
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # User agent
    options.add_argument(
        'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )

    return options


def apply_stealth_to_selenium_driver(driver):
    """
    Apply stealth modifications to Selenium driver.

    Args:
        driver: Selenium WebDriver instance

    Returns:
        Modified driver
    """
    # Override navigator.webdriver
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    # Override chrome property
    driver.execute_script(
        "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})"
    )

    # Override languages
    driver.execute_script(
        "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})"
    )

    return driver


async def apply_stealth_to_playwright_page(page):
    """
    Apply stealth modifications to Playwright page.

    Args:
        page: Playwright Page instance

    Returns:
        Modified page
    """
    # Override navigator.webdriver
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    # Override chrome property
    await page.add_init_script("""
        window.navigator.chrome = {
            runtime: {},
        };
    """)

    # Override permissions
    await page.add_init_script("""
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """)

    # Override plugins
    await page.add_init_script("""
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
    """)

    return page
