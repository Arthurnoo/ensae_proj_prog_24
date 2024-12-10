import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL de la page à scraper
url = "https://www.moka-mag.com/articles/le-top-10-des-plus-grands-festivals-musicaux-de-france"

# Envoyer une requête HTTP pour récupérer le contenu de la page
response = requests.get(url)
if response.status_code == 200:
    print("Page chargée avec succès")
else:
    print(f"Erreur lors du chargement de la page : {response.status_code}")
    exit()

# Parser le contenu HTML avec BeautifulSoup
soup = BeautifulSoup(response.content, "html.parser")

# Trouver les sections contenant les informations sur les festivals
festival_sections = soup.find_all("div", class_="text-block-left")

# Extraire les données
festivals = []
for section in festival_sections:
    try:
        # Extraire le nom du festival
        title_tag = section.find("h3")
        title = title_tag.text.strip() if title_tag else "N/A"
        
        # Extraire le lieu
        location_tag = section.find("strong", string=lambda s: s and "Où" in s)
        location = location_tag.find_next("a").text.strip() if location_tag else "N/A"
        
        # Extraire la date
        date_tag = section.find("strong", string=lambda s: s and "Quand" in s)
        date = date_tag.next_sibling.strip() if date_tag and date_tag.next_sibling else "N/A"
        
        # Ajouter les données dans la liste
        festivals.append({"Nom": title, "Lieu": location, "Date": date})
    except Exception as e:
        print(f"Erreur lors de l'extraction d'une section : {e}")

# Convertir en DataFrame
df = pd.DataFrame(festivals)

# Sauvegarder dans un fichier CSV
if not df.empty:
    df.to_csv("festivals_moka_mag.csv", index=False, encoding="utf-8")
    print("Les données ont été sauvegardées dans 'festivals_moka_mag.csv'.")
else:
    print("Aucune donnée trouvée.")

# Afficher les données dans la console
print(df)
