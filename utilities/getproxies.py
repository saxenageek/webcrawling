from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def get_proxies():
    options = Options()
    options.add_argument('--headless')  # Runs Chrome in headless mode.
    options.add_argument('--no-sandbox')  # Bypass OS security model
    options.add_argument('start-maximized')
    options.add_argument('disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_argument("--disable-gpu")
    options.add_argument('--no-proxy-server')
    options.add_argument('disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=fake-useragent')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options, service_log_path='/dev/null')

    # Get free proxies for rotating
    # def get_proxies(driver):
    proxies = []
    try:
        driver.get('https://sslproxies.org')

        table = driver.find_element(By.TAG_NAME, 'table')
        thead = table.find_element(By.TAG_NAME, 'thead').find_elements(By.TAG_NAME, 'th')
        tbody = table.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')

        headers = []
        for th in thead:
            headers.append(th.text.strip())

        proxies = []
        for tr in tbody:
            proxy_data = {}
            tds = tr.find_elements(By.TAG_NAME, 'td')
            # proxy_data[headers[i]] = tds[i].text.strip()
            for i in range(len(headers)):
                proxy_data[headers[i]] = tds[i].text.strip()
                if 'Country' in proxy_data:
                    if proxy_data['Country'] in ['United States','India']:
                        if 'Https' in proxy_data:
                            if proxy_data['Https'] == "yes":                
                                proxy = proxy_data['IP Address']
                                if 'Port' in proxy_data:
                                    proxy += ':' + proxy_data['Port']
                                proxies.append(proxy)
    except Exception as e:
        print("Proxy retrieval failed", str(e))
        pass

    return proxies

get_proxies()
