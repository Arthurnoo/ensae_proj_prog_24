from playwright.sync_api import sync_playwright
import pandas as pd

def scrape_festival_data():
    # URL de l'iframe
    iframe_url = "https://touslesfestivals.carto.com/builder/98261f7f-d959-4268-8a60-35f85bd4"

    # Liste pour stocker les données
    festivals = []

    # Utiliser Playwright pour accéder à la page
    with sync_playwright() as p:
        # Lancer le navigateur Chromium en mode headless
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Aller à l'URL de l'iframe
        page.goto(iframe_url)

        # Vérifier le contenu HTML (pour débogage)
        print("Contenu HTML chargé :")
        print(page.content())  # Affiche le HTML chargé dans la console

        # Extraire les données
        try:
            tooltip_items = page.query_selector_all(".CDB-Tooltip-listItem")
            for item in tooltip_items:
                title = item.query_selector(".CDB-Tooltip-listTitle").inner_text()
                text = item.query_selector(".CDB-Tooltip-listText").inner_text()
                festivals.append({"title": title, "text": text})
        except Exception as e:
            print(f"Erreur lors du scraping : {e}")

        # Fermer le navigateur
        browser.close()

    return festivals


# Main
if __name__ == "__main__":
    print("Scraping des données des festivals...")
    scraped_data = scrape_festival_data()

    print(f"Nombre de festivals extraits : {len(scraped_data)}")
    for festival in scraped_data[:5]:  # Afficher les 5 premiers
        print(f"Titre : {festival['title']}, Texte : {festival['text']}")

    # Sauvegarder les données dans un fichier CSV
    if scraped_data:
        df = pd.DataFrame(scraped_data)
        df.to_csv("festivals_playwright.csv", index=False, encoding="utf-8")
        print("Les données ont été sauvegardées dans 'festivals_playwright.csv'.")
