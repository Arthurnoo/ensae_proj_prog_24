import requests
from bs4 import BeautifulSoup
import pandas as pd

# Fonction pour charger une page web
def charger_page(url):
    response = requests.get(url)
    if response.status_code == 200:
        print("Page chargée avec succès")
        return response.content
    else:
        print(f"Erreur lors du chargement de la page : {response.status_code}")
        return None

# Fonction pour extraire les données des festivals
def extraire_donnees_festivals(html):
    soup = BeautifulSoup(html, "html.parser")
    sections_festivals = soup.find_all("div", class_="text-block-left")
    
    festivals = []
    for section in sections_festivals[1:]:
        try:
            # Nom du festival
            titre = section.find("h3").text.strip() if section.find("h3") else "N/A"
            
            # Lieu du festival
            lieu_tag = section.find("strong", string=lambda s: s and "Où" in s)
            lieu = lieu_tag.find_next("a").text.strip() if lieu_tag else "N/A"
            
            # Date du festival
            date_tag = section.find("strong", string=lambda s: s and "Quand" in s)
            date = date_tag.next_sibling.strip() if date_tag and date_tag.next_sibling else "N/A"
            
            festivals.append({"Nom": titre, "Lieu": lieu, "Date": date})
        except Exception as e:
            print(f"Erreur lors de l'extraction des données d'une section : {e}")
    return festivals

# Fonction pour sauvegarder les données dans un fichier CSV
def sauvegarder_donnees_csv(festivals, fichier):
    df = pd.DataFrame(festivals)
    if not df.empty:
        df.to_csv(fichier, index=False, encoding="utf-8")
        print(f"Les données ont été sauvegardées dans '{fichier}'.")
    else:
        print("Aucune donnée à sauvegarder.")
    return df

# URL de la page cible
url = "https://www.moka-mag.com/articles/le-top-10-des-plus-grands-festivals-musicaux-de-france"

# Étapes du processus
html = charger_page(url)
if html:
    festivals = extraire_donnees_festivals(html)
    df = sauvegarder_donnees_csv(festivals, "festivals_moka_mag.csv")
    print(df)
    
