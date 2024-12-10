import random
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pandas as pd
from io import StringIO

# Configuration des en-têtes pour Selenium
CHROME_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}
print(driver.page_source)


# Fonction pour récupérer et valider une liste de proxys
def get_valid_proxies():
    response = requests.get("https://free-proxy-list.net/")
    html_data = StringIO(response.text)
    proxy_list = pd.read_html(html_data)[0]
    proxy_list["url"] = "http://" + proxy_list["IP Address"] + ":" + proxy_list["Port"].astype(str)
    https_proxies = proxy_list[proxy_list["Https"] == "yes"]["url"].tolist()

    good_proxies = []
    test_url = "http://httpbin.org/ip"
    for proxy in https_proxies:
        try:
            proxies_dict = {"http": proxy, "https": proxy}
            response = requests.get(test_url, headers=CHROME_HEADERS, proxies=proxies_dict, timeout=5)
            if response.status_code == 200:
                good_proxies.append(proxy)
                print(f"Proxy {proxy} valide.")
        except:
            pass
        if len(good_proxies) >= 10:  # Limiter à 10 proxys fonctionnels
            break
    return good_proxies

# Initialiser Selenium WebDriver
def get_driver(proxy=None, headless=True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    if proxy:
        chrome_options.add_argument(f"--proxy-server={proxy}")
    return webdriver.Chrome(options=chrome_options)

# Scraper les données de l'iframe
def scrape_festival_data(proxies):
    proxy = random.choice(proxies)
    driver = get_driver(proxy=proxy)
    iframe_url = "https://touslesfestivals.carto.com/builder/98261f7f-d959-4268-8a60-35f85bd4"
    driver.get(iframe_url)

    # Attendre le chargement de la page
    time.sleep(10)

    # Extraire les données
    festivals = []
    try:
        tooltip_items = driver.find_elements(By.CLASS_NAME, "CDB-Tooltip-listItem")
        for item in tooltip_items:
            title = item.find_element(By.CLASS_NAME, "CDB-Tooltip-listTitle").text
            text = item.find_element(By.CLASS_NAME, "CDB-Tooltip-listText").text
            festivals.append({"title": title, "text": text})
    except Exception as e:
        print(f"Erreur lors du scraping : {e}")

    driver.quit()
    return festivals

# Main
if __name__ == "__main__":
    print("Récupération des proxys valides...")
    valid_proxies = get_valid_proxies()

    print("Scraping des données des festivals...")
    scraped_data = scrape_festival_data(valid_proxies)

    print(f"Nombre de festivals extraits : {len(scraped_data)}")
    for festival in scraped_data[:5]:  # Afficher les 5 premiers
        print(f"Titre : {festival['title']}, Texte : {festival['text']}")

    # Sauvegarder les données dans un fichier CSV
    if scraped_data:
        df = pd.DataFrame(scraped_data)
        df.to_csv("festivals.csv", index=False, encoding="utf-8")
        print("Les données ont été sauvegardées dans 'festivals.csv'.")
