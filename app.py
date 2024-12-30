import subprocess
import sys

# Installer les packages nécessaires
def install_packages():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "folium"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit-folium"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])

# Appeler la fonction pour installer les packages
install_packages()

# Importation des modules nécessaires
import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import pandas as pd

# Charger les données utilisateur collectées
try:
    with open("user_data.json", "r") as json_file:
        user_data = json.load(json_file)
        print("Données utilisateur récupérées :", user_data)
except FileNotFoundError:
    st.error("Aucune donnée utilisateur n'a été collectée. Lancez 'questions.py' pour collecter les données.")
    user_data = {"coordinates": [48.8566, 2.3522]}  # Coordonnées par défaut (Paris)

# Charger les festivals depuis le fichier CSV
df_end = pd.read_csv('df_end.csv')

# Vérifier si df_end est vide
if df_end.empty:
    st.title("Carte des Festivals en France")
    st.error("Aucun festival trouvé avec les critères donnés. Veuillez élargir vos choix pour découvrir d'autres festivals.")
else:
    # Fonction pour décaler légèrement les marqueurs en cas de doublon
    def ajuster_coordonnees(festivals):
        """
        Décale légèrement les coordonnées pour les festivals ayant les mêmes positions géographiques.
        """
        coords_count = {}
        for i, row in festivals.iterrows():
            coords = row['Géocodage xy'].strip()
            if coords not in coords_count:
                coords_count[coords] = 0
            else:
                coords_count[coords] += 1
            
            # Décaler légèrement la position
            lat, lon = map(float, coords.split(','))
            offset = coords_count[coords] * 0.005  # Décalage minime
            lat += offset
            lon += offset
            festivals.at[i, 'Géocodage xy'] = f"{lat},{lon}"
        return festivals

    # Appliquer l'ajustement des coordonnées
    df_end = ajuster_coordonnees(df_end)

    # Fonction pour afficher les festivals sur une carte
    def afficher_festivals_sur_carte(festivals, user_location):
        """
        Affiche les festivals sur une carte interactive avec l'adresse de l'utilisateur.
        """
        carte = folium.Map(location=user_location, zoom_start=6, tiles="OpenStreetMap")
        
        # Ajouter un marqueur pour l'utilisateur
        folium.Marker(
            location=user_location,
            popup=f"<b>Votre adresse</b>",
            tooltip="Votre position 📍",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(carte)
        
        # Ajouter un marqueur pour chaque festival
        for _, row in festivals.iterrows():
            try:
                # Extraire les coordonnées depuis la colonne 'Géocodage xy'
                lat, lon = map(float, row['Géocodage xy'].split(','))
            except (ValueError, AttributeError):
                continue  # Ignorer si les coordonnées ne sont pas valides

            nom = row['Nom du festival']
            date = row['Période principale de déroulement du festival']
            description = f"{row['Discipline dominante']} - {row['Envergure territoriale']}"
            lien = row['Site internet du festival'] if pd.notna(row['Site internet du festival']) else "#"

            # Ajouter un marqueur avec popup
            popup_content = f"""
            <b>{nom}</b><br>
            Date : {date}<br>
            {description}<br>
            <a href="{lien}" target="_blank" style="color:blue; text-decoration:underline;">Lien vers le site</a>
            """
            folium.Marker(
                location=[lat, lon],
                popup=popup_content,
                tooltip=nom,
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(carte)
        
        return carte

    # Utiliser la localisation de l'utilisateur
    user_location = user_data['coordinates']

    # Titre dans Streamlit
    st.title("Carte des Festivals en France")

    # Générer la carte
    carte = afficher_festivals_sur_carte(df_end, user_location)

    # Afficher la carte interactive avec Streamlit
    map_result = st_folium(carte, width=800, height=600)

    # Afficher les informations du festival sélectionné
    if map_result and map_result.get('last_object_clicked'):
        lat = map_result['last_object_clicked']['lat']
        lon = map_result['last_object_clicked']['lng']

        # Rechercher le festival correspondant
        for _, row in df_end.iterrows():
            festival_lat, festival_lon = map(float, row['Géocodage xy'].split(','))
            if abs(festival_lat - lat) < 0.0001 and abs(festival_lon - lon) < 0.0001:
                st.subheader(f"Informations sur {row['Nom du festival']}")
                st.write(f"**Date** : {row['Période principale de déroulement du festival']}")
                st.write(f"**Description** : {row['Discipline dominante']} - {row['Envergure territoriale']}")
                lien = row['Site internet du festival']
                if pd.notna(lien):
                    st.write(f"[Site du festival]({lien})")
                break