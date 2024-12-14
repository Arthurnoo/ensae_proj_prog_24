import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL de la page
url = "https://infoconcert.com/festival/les-plus-consultes.html"

# Envoyer une requête HTTP
response = requests.get(url)
if response.status_code == 200:
    print("Page chargée avec succès")
else:
    print(f"Erreur lors du chargement de la page : {response.status_code}")
    exit()

# Parser le contenu HTML avec BeautifulSoup
soup = BeautifulSoup(response.content, "html.parser")

# Trouver les sections correspondant aux festivals
festival_rows = soup.find_all("div", class_="row")

# Extraire les données
festivals = []
seen = set()  # Pour éviter les doublons
for row in festival_rows:
    try:
        # Classement
        ranking_tag = row.find("span", class_="top-position-number")
        ranking = ranking_tag.text.strip() if ranking_tag else None

        # Nom du festival
        name_tag = row.find("div", class_="top-line-name").find("a")
        name = name_tag.text.strip() if name_tag else None
        link = f"https://infoconcert.com{name_tag['href']}" if name_tag else None

        # Lieu
        location_tag = row.find("div", class_="top-coming-concerts")
        location = location_tag.text.strip() if location_tag else None

        # Vérifier que les données sont complètes et uniques
        if name and ranking and (ranking, name) not in seen:
            festivals.append({
                "Classement": ranking,
                "Nom": name,
                "Lieu": location,
                "Lien": link
            })
            seen.add((ranking, name))  # Marquer comme vu
    except Exception as e:
        print(f"Erreur lors de l'extraction d'une ligne : {e}")

# Convertir en DataFrame
df = pd.DataFrame(festivals)

# Supprimer les doublons au cas où
df = df.drop_duplicates()

# Sauvegarder les données dans un fichier CSV
if not df.empty:
    df.to_csv("top_50_festivals.csv", index=False, encoding="utf-8")
    print("Les données ont été sauvegardées dans 'top_50_festivals.csv'.")
else:
    print("Aucune donnée trouvée.")

# Afficher un aperçu des données
print(df)

# Nettoyer la colonne "Lieu"
df['Lieu'] = df['Lieu'].str.replace(r'\n\(.*?\)', '', regex=True).str.strip()

# Vérifier le résultat
print(df[['Classement', 'Nom', 'Lieu']].head())



from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="festival_scraper")

def geocode_location(location):
    try:
        geo = geolocator.geocode(location)
        if geo:
            return geo.latitude, geo.longitude
        else:
            return None, None
    except Exception as e:
        print(f"Erreur de géocodage pour {location}: {e}")
        return None, None

# Ajouter des colonnes Latitude et Longitude
df[['Latitude', 'Longitude']] = df['Lieu'].apply(lambda x: pd.Series(geocode_location(x)))

# Supprimer les lignes sans coordonnées
df = df.dropna(subset=['Latitude', 'Longitude'])

import folium

# Créer une carte centrée sur la France
map_festivals = folium.Map(location=[46.603354, 1.888334], zoom_start=6)

# Ajouter des marqueurs pour chaque festival
for _, row in df.iterrows():
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=row['Nom']
    ).add_to(map_festivals)

# Sauvegarder la carte
map_festivals.save("map_top_50_festivals.html")
print("Carte sauvegardée sous 'map_top_50_festivals.html'")


import os
print("Carte sauvegardée ici :", os.path.abspath("map_top_50_festivals.html"))

map_festivals.save("/home/onyxia/work/map_top_50_festivals.html")

map_festivals.save("/home/onyxia/work/map_top_50_festivals.html")

import folium

# Exemple de carte
map_festivals = folium.Map(location=[46.603354, 1.888334], zoom_start=6)
map_festivals.save("map_top_50_festivals.html")

# Afficher dans un notebook
from IPython.display import IFrame

IFrame("map_top_50_festivals.html", width=800, height=600)






