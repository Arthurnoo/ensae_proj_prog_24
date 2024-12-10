from playwright.sync_api import sync_playwright
import pandas as pd

# URL de la page contenant le graphique
url = "https://touslesfestivals.com/actualites/le-bilan-des-festivals-de-lannee-2022-lannee-de-reprise-110123"

def scrape_festival_data():
    with sync_playwright() as p:
        # Lancer le navigateur
        browser = p.chromium.launch(headless=True, args=["--ignore-certificate-errors"])
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        # Charger la page
        page.goto(url)
        page.wait_for_timeout(5000)  # Attendre 5 secondes pour le chargement

        # Sélectionner toutes les balises <path> avec des données
        paths = page.query_selector_all("path[aria-label]")
        festivals = []

        for path in paths:
            aria_label = path.get_attribute("aria-label")
            if aria_label:  # Vérifier que l'attribut est non vide
                try:
                    # Extraire le nom du festival et la valeur
                    name, value = aria_label.split(":")
                    festivals.append({"Festival": name.strip(), "Valeur": value.strip()})
                except ValueError:
                    print(f"Erreur lors de l'analyse de : {aria_label}")

        browser.close()

        # Convertir en DataFrame
        df = pd.DataFrame(festivals)
        print(df)

        # Sauvegarder les données dans un fichier CSV
        if not df.empty:
            df.to_csv("festivals_data.csv", index=False, encoding="utf-8")
            print("Les données ont été sauvegardées dans 'festivals_data.csv'.")
        else:
            print("Aucune donnée trouvée.")

# Appeler la fonction
scrape_festival_data()
